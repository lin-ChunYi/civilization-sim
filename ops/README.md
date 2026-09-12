# ops/ —— Cockpit 薄接力入口

一个文件（`dispatch.py`，标准库、Python 3.9+、无第三方依赖）+ 一套定向测试。
它**只管队列与回执**：把已批准的派工投进本机 Cockpit hub 的 outbox、持续收结果、落盘、
整理出一份脱敏 STATUS。

**它不做独立验收。** 助手自己回的 `CIV_RESULT_*` 最多让任务停在 `review`；
真正的 `done` 必须由外部（已经在跑的 Codex 主控 / 5 分钟心跳）带证据执行 `accept`。
这不是谦虚，是设计约束：自证不能当验收。

它也**不会**：杀或关闭任何用户自己的会话、自动重发结果未知的投递、绕过权限或额度、
开网络端口、起服务、引入 Redis / 队列中间件 / Agent 平台。

## 快速开始

```bash
# 看一眼当前状态（只读，不派单）
python3 ops/dispatch.py status

# 登记一个已批准的任务（job JSON 见下）
python3 ops/dispatch.py submit ops/jobs/C03.json

# 前台守护（收结果 + 到点派单），Ctrl+C 退出
python3 ops/dispatch.py watch --interval 20

# 或者后台守护（同一项目只允许一个）
python3 ops/dispatch.py start --interval 20
python3 ops/dispatch.py stop
```

默认路径：状态目录 `<repo>/.dispatch`（项目内，不进版本库），
hub 目录 `$COCKPIT_HUB_DIR`，没设就是 `~/.cockpit/hub`。两个都可以用
`--state-dir` / `--hub-dir` 换成任意绝对路径（测试就是这么做的）。

## 暂停与恢复

```bash
python3 ops/dispatch.py pause     # 立刻拦住新派单
python3 ops/dispatch.py resume
```

`pause` 做两件事，仅此两件：

1. **立刻**阻止再派出任何新任务；
2. 对**本调度登记过、且仍在运行**的回合，发**一次**协作式请求："请在下一个安全点停下"。

它**不会**打断当前这一步，**不会**杀进程、**不会**关会话，也**不承诺**立刻中断 ——
对方什么时候停、停不停，要看它自己的回执或会话回到 `waiting`。通知只发一次，
`resume` 之后才会重新允许发。

`stop` 只停**本脚本自己启动的 watch 进程**，而且**先验明正身**：
`watch.json` 里记了 pid + 一次性 token，`stop` 会用 `ps` 核对那个 pid 确实是
"本脚本、本 state-dir 的 watch"。核对不上（典型是 pid 被别的进程复用、或 `ps` 不可用）
就**不发信号**，只报告让人去看 —— 宁可留个孤儿状态文件，也不能误杀别人的进程。
确认之后才写带 token 的 `stop.request` 并发 SIGTERM，等它把状态写完退出。
它不碰任何被借用的会话，也不会留下第二个还在派单的控制器。

守护和独立命令共用一把项目锁，但行为不同：**守护会等**（默认最多 10 秒，`--lock-wait` 可调），
等不到就**跳过这一轮继续活着**（`watch.json` 里记 `skipped_rounds`）；
独立命令不等，直接如实报 `busy`（退出码 3）。一次正常的 `status`/`submit`/`pause`
不会把守护弄退出。

## 状态与回执怎么读

`status` / 每轮 watch 都会写 `<state-dir>/STATUS.md` 与 `STATUS.json`（脱敏）：
当前任务、下一项、提交号、实测命令、截图、阻塞原因。
**完整提示词与转录正文只留在 `<state-dir>/logs/*`（0600），STATUS 里一个字都没有。**

### 自报报告是**数据**，不是约定好的结构

`CIV_RESULT_<任务> {...}` 后面那段 JSON 是 agent 自己写的。约定里 `tests` / `screenshots`
是列表，但实际接力里它可能是对象、字符串、数字、`null`，甚至整段不是对象。
**显示层对任何类型都必须给得出结果**：

- 原始报告一个字不改地留在 `queue.json` 的 `job.report` 里 —— 摘要只是摘要，要看全的看它。
- `STATUS` 里的 `tests` / `screenshots` 一律是**字符串列表**：对象按 `键: 值` 展开、
  标量转成一行文本、`null` 给空列表。条数超过 6 条时末尾补"另有 N 项"，**不静默丢**。
- 显示层只做 `str()` / `json.dumps()`：**不对原始对象取下标或切片、不格式化、不求值、
  不执行**里面的任何内容。
- 报告整段不是对象时，行里标 `report_note: report is not an object: …`，
  不去猜它想说什么。
- **自报永远只到 `review`。** 报告格式再标准也不是验收，`done` 必须由外部
  `accept --evidence` 带证据给。

一条任务的报告畸形或元数据渲染不出来时，只标这一条（`render_error` / `collect_error`），
**其余任务照常收取与显示，守护继续活着**。C04 之前不是这样：`tests[:6]` 在一个对象上
直接抛异常（Python 3.12 是 `KeyError: slice(...)`，更早的版本是
`TypeError: unhashable type: slice`），整个 watch 跟着退出。

轮次级还有最后一道兜底网：一轮里出了完全没预料到的异常，记进
`<state-dir>/logs/watch-errors.jsonl`（0600）与 `watch.json` 的 `error_rounds`，
下一轮继续。**它不覆盖坏队列那条规则** —— `queue.json` 读不出来仍然是保留原件、
拦住派发、报 `blocked`，不会被当成"意外异常"含糊过去。

投递结果分成互不含糊的几类，别混着看：

| receipt_state | 含义 |
|---|---|
| `queued` | 信封已落 outbox / 已被取走，还没有终态回执 |
| `bridge_ack` | 桥接确认收到 —— **不是**任务完成 |
| `durable_ok` | 终态回执 `ok:true` —— 只代表**送达**，仍然不是完成 |
| `permission_pending` | 对面有权限/提问待办，需要人去看，不要一键批准 |
| `failed` | 明确失败（`ok:false` 或 `.err`） |
| `quota_blocked` | 明确的额度/限流阻塞 —— 不切付费通道、不高速重试 |
| `unknown` | **结果未知**：超时没有终态回执、`agent_prompt_stalled`、或回执写了一半读不出来。不是失败，**绝不自动重发** |

两点容易搞错，写清楚：

* **`agent_prompt_stalled` 不是失败。** 它的意思是文字和回车**都已经送到**，
  只是没看见画面推进。当成失败去重排，就是把同一份活儿派了两遍。
* **超时判定不看 outbox 里还剩什么。** 信封没被取走、或者只有一个 `.ack`，
  到点照样判 `unknown` —— 否则会永远停在 `queued`/`bridge_ack` 等一个不会来的回执。

任务状态：`pending → running → review →（外部 accept）→ done`，
出问题则 `blocked`。`unknown` 只会让任务 `blocked` 停下等人看。

要重排一个任务：

```bash
# 免确认重排，**只允许**能证明"根本没送到对面"的失败
# （session not found / device offline / invalid envelope / rejected before delivery …）
python3 ops/dispatch.py requeue C03

# 其余一律要显式承认重复投递风险：unknown、agent_prompt_stalled、
# 半写回执、以及原因不明的 ok:false
python3 ops/dispatch.py requeue C03 --acknowledge-duplicate-risk
```

## 返工闭环（不要手改 queue.json）

外部复核认为不合格时，有两条**受控**路径，不需要去编辑状态文件：

```bash
# 1) 直接拒收：review/blocked -> rejected，owner 随之释放，可以接下一个任务
python3 ops/dispatch.py reject G01 --reason "独立复核发现 X"

# 2) 或者保留 review，派一个明确指向它的返工任务（job JSON 里写 "rework_of": "G01"）
python3 ops/dispatch.py submit ops/jobs/G01_R1.json
```

`rework_of` 必须指向**同一个 owner**、且处于 `review` / `rejected` / `blocked` 的那条任务；
只有它能在 owner 还压着 review 的时候被派出去。**普通的下一个任务仍然要等 `accept`**，
这条规矩没有松。

两条边界也写死了：**一个 tick 最多派一份返工**（两条都指向同一个 review 的返工同时排队时，
派出第一份后本轮的占用身份立刻换成它，第二份等下一轮再说）；
**同 owner 已经有任务在跑时，返工也不能插队**（占位身份按 running > blocked > review 取）。

## 转录被截短了怎么办（已处理）

`request_transcript(tail_bytes)` 会把本机物化的转录文件**截短重写**，
派工时记下的字节偏移立刻失效。脚本用双保险处理：

1. 派工时除了偏移，还记一个锚（偏移前 512 字节的 sha256）。锚对得上就走快路；
2. 对不上就**重新绑定**，按三件真实情况处理：
   * 每次投递都带一个唯一前缀 `[dispatch <TASK_ID> <CORR8>]`，重绑定找的是**它**，
     所以上一轮的同名标记冒充不了这一轮；
   * Cockpit 的 `composeInjection` 会把 CR/LF/Tab 折成空格
     （`cockpit-cloud-hub/internal/inject/attachment.go:94`），
     所以两边都按同一套**空白规范化**再比；
   * Grok 会把用户提示词拆成多条 `user chunk`，所以连续的用户记录先**原样**拼起来、
     再统一做空白规范化 —— 中间补空格会把跨 chunk 的 tag（`[dispa` + `tch T1 …`）
     拼成 `[dispa tch T1 …` 而找不到。Claude 的每条 text 是独立消息，保留换行分隔，
     两种格式不混用。
   找不到就报 `rebind-failed`，宁可等人看，也不拿孤立的标记当完成。

配套的两条硬规矩：**只认助手说的话**（派工提示词里本来就带着 `CIV_RESULT_` 模板，
它是用户记录，永远不算完成），**只认本次派工之后**的输出（上一轮遗留的同名标记不算）。
两种真实格式都认：Claude 的 `assistant.message.content[].text` 整块，
以及 Grok ACP 的 `agent_message_chunk`（同一句话可能被拆成多条，必须原样拼回）。

## 任务 JSON 需要哪些字段

`task_id`（大写下划线）、`owner`（`claude` / `grok`）、`objective`、`allowed_paths`、
`baseline_sha`、`dependencies`、`acceptance`、`workdir`、`branch`、
`device_id`、`session_id`、`session_cwd`、`prompt_file`；
可选 `rework_of`（指向同 owner 的 review/rejected/blocked 任务，用于受控返工）。
派工前会核对会话身份（source / cwd）与空闲边界，对不上就不投。

## 测试

```bash
python3 ops/test_dispatch.py      # 35 项，全部在临时目录里造假 hub
```

不碰本机任何真实会话与真实 outbox（PID 复用那条也只拿测试自己起的 `sleep` 当靶子）。
覆盖：假助手标记、只认派工之后的输出、两种 chunk 格式、截短后重绑定
（含真实空白规范化与 Grok 拆 chunk）、旧投递前缀不可冒充、回执分级、
`agent_prompt_stalled` 与半写回执判 unknown、留着 ack/信封也能按时判 unknown、
安全重排的边界、不重发与重启、并发锁下守护存活、暂停只通知一次、
`stop` 拒绝对身份不明的 pid 发信号、损坏 queue.json 保留原件并拦住派发、
拒收/返工闭环、`screenshots[]`、自报不等于验收、STATUS 脱敏、
自报报告的类型边界（R21 组：真实 C03 报告里 `tests` 是对象、字符串/数字/布尔/`null`/
嵌套对象/坏可选字段、报告整段不是对象、单条任务渲染失败不连累其他任务、
收取失败按任务记录、**真守护子进程收到对象型 `tests` 后仍然活着并继续派下一个任务**、
轮次异常不杀守护也不丢队列、坏队列仍按原规则保留）。

每条都验证过"把对应防护去掉就会红"：把这 35 项拿去跑 `aff0ed5` 会红 13 项，
跑 `3abe009` 会红 3 项（跨 chunk 的 tag、同 tick 两份返工、running 被返工插队），
跑 `4168356`（C04 之前）会红 15 项（3 failures + 12 errors）。

## 边界（写明，别指望）

- **独立验收不在这里**：由已经在跑的 Codex 主控或它的心跳任务承担。
- **关机 / 应用退出不保证继续**：watch 是一个普通前台/后台进程，没有 launchd、
  没有系统服务、没有自启。机器睡了、终端关了、Cockpit 应用退了，它就停了；
  重启后要人手 `start`，而且**不会**自动重发结果未知的任务。
- **状态文件坏了不会被悄悄覆盖**：`queue.json` 读不出来时会把原件另存为
  `queue.corrupt.<时间戳>.json`，然后拦住一切派发并报 `blocked`（退出码 2），
  等人修好，绝不拿一个空队列写回去。
- **报告内容不做真伪判断**：类型归一化只保证"显示得出来、不打死守护"，
  它不检查 commit 是否存在、测试是否真跑过。那是独立验收的事。
- 没有网络端口、没有远程命令入口。
- 不新建 Redis / 微服务 / Agent 平台，这个文件就是全部。
