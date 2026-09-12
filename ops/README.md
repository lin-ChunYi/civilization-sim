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

`stop` 只停**本脚本自己启动的 watch 进程**：先落 `stop.request`，再发 SIGTERM，
等它把状态写完退出。它不碰任何被借用的会话，也不会留下第二个还在派单的控制器。

## 状态与回执怎么读

`status` / 每轮 watch 都会写 `<state-dir>/STATUS.md` 与 `STATUS.json`（脱敏）：
当前任务、下一项、提交号、实测命令、截图、阻塞原因。
**完整提示词与转录正文只留在 `<state-dir>/logs/*`（0600），STATUS 里一个字都没有。**

投递结果分成互不含糊的几类，别混着看：

| receipt_state | 含义 |
|---|---|
| `queued` | 信封已落 outbox / 已被取走，还没有落地回执 |
| `bridge_ack` | 桥接确认收到 —— **不是**任务完成 |
| `durable_ok` | 落地回执 `ok:true` —— 只代表**送达**，仍然不是完成 |
| `permission_pending` | 对面有权限/提问待办，需要人去看，不要一键批准 |
| `failed` | 明确失败（`ok:false` 或 `.err`） |
| `quota_blocked` | 明确的额度/限流阻塞 —— 不切付费通道、不高速重试 |
| `unknown` | 超时仍无回执：**结果未知**。不是失败，也**绝不自动重发** |

任务状态：`pending → running → review →（外部 accept）→ done`，
出问题则 `blocked`。`unknown` 只会让任务 `blocked` 停下等人看。

要重排一个任务：

```bash
python3 ops/dispatch.py requeue C03                               # 仅限明确失败
python3 ops/dispatch.py requeue C03 --acknowledge-duplicate-risk  # 未知投递，必须显式承认风险
```

## 转录被截短了怎么办（已处理）

`request_transcript(tail_bytes)` 会把本机物化的转录文件**截短重写**，
派工时记下的字节偏移立刻失效。脚本用双保险处理：

1. 派工时除了偏移，还记一个锚（偏移前 512 字节的 sha256）。锚对得上就走快路；
2. 对不上就**重新绑定**：在当前文件里找到最后一条包含本次提示词开头的**用户**记录，
   只认它之后的**助手**记录。找不到就报 `rebind-failed`，宁可等人看，
   也不拿孤立的标记当完成。

配套的两条硬规矩：**只认助手说的话**（派工提示词里本来就带着 `CIV_RESULT_` 模板，
它是用户记录，永远不算完成），**只认本次派工之后**的输出（上一轮遗留的同名标记不算）。
两种真实格式都认：Claude 的 `assistant.message.content[].text` 整块，
以及 Grok ACP 的 `agent_message_chunk`（同一句话可能被拆成多条，必须原样拼回）。

## 任务 JSON 需要哪些字段

`task_id`（大写下划线）、`owner`（`claude` / `grok`）、`objective`、`allowed_paths`、
`baseline_sha`、`dependencies`、`acceptance`、`workdir`、`branch`、
`device_id`、`session_id`、`session_cwd`、`prompt_file`。
派工前会核对会话身份（source / cwd）与空闲边界，对不上就不投。

## 测试

```bash
python3 ops/test_dispatch.py      # 13 项，全部在临时目录里造假 hub
```

不碰本机任何真实会话与真实 outbox。覆盖：假助手标记、只认派工之后的输出、
两种 chunk 格式、截短后重绑定与无法绑定、回执分类、不重发与重启、并发锁、
暂停只通知一次、安全停止、自报不等于验收、STATUS 脱敏。
每条都验证过"把对应防护去掉就会红"。

## 边界（写明，别指望）

- **独立验收不在这里**：由已经在跑的 Codex 主控或它的心跳任务承担。
- **关机 / 应用退出不保证继续**：watch 是一个普通前台/后台进程，没有 launchd、
  没有系统服务、没有自启。机器睡了、终端关了、Cockpit 应用退了，它就停了；
  重启后要人手 `start`，而且**不会**自动重发结果未知的任务。
- 没有网络端口、没有远程命令入口。
- 不新建 Redis / 微服务 / Agent 平台，这个文件就是全部。
