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

## 另一条通道：`transport: "grok-cli"`

默认通道把提示词投进 Cockpit 的 outbox（`reply_inject`）。另一条通道直接以
**订阅版 headless CLI** 跑一轮，两条并存，按任务选。

```json
{
  "task_id": "G03_FIX", "owner": "grok", "transport": "grok-cli",
  "objective": "...", "allowed_paths": ["observer/web/"], "baseline_sha": "...",
  "dependencies": [], "acceptance": "...", "workdir": "/path/to/repo",
  "branch": "main", "prompt_file": "STATE/prompts/G03_FIX.txt",
  "cli": {
    "bin": "/Users/ecool/.grok/bin/grok",
    "cwd": "/Users/ecool/Desktop/civilization/civilization-sim",
    "session_id": "041d93f0-5eae-4cff-90b8-f52785f14553",
    "output_format": "json",
    "permission_mode": "acceptEdits",
    "allow": ["Bash(git status*)", "Bash(git diff*)", "Bash(git log*)",
              "Bash(git add observer/web/*)", "Bash(git commit*)",
              "Bash(node --check observer/web/*)", "Bash(rg *)", "Bash(ls observer/web*)",
              "Edit(/abs/path/observer/web/**)", "Edit(observer/web/**)"],
    "deny": ["Bash(git push*)"],
    "max_turns": 100,
    "extra_args": ["--no-subagents", "--disable-web-search"],
    "graceful_cancel": false
  }
}
```

命令数组是**按这些字段逐项拼出来的**，一字不多，落盘在 `logs/<任务>.command.json`，
不过 shell、没有隐藏默认值。`session_id` 有就是 `--resume <uuid>`（续用会话），
没有就是新建会话（会话 id 从它自己的输出里记回来）。

**权限规则必须逐条写明。** `--permission-mode acceptEdits` 并**不**自动批准编辑类工具：
实测 `search_replace` 仍会被 `PermissionCancelled` 挡下来，加上显式的
`Edit(observer/web/**)`（以及同路径的绝对写法）之后才真的写进了文件。
按官方文档，`Edit` 的规则是按工具传入的 path glob 匹配的，绝对与相对都该覆盖，
没有 `//` 或 `~/` 那种锚定语义。所以：**不要把 `acceptEdits` 当成够用**，
最终的权限表由主控实测之后登记。

实测登记到目前为止（由主控核实，规则会继续长）：
`git status` / `git diff` / `git log` / `git rev-parse` / `git show`、
`git add observer/web`（目录本身）及其子文件、`git commit`（**必须单行 literal `-m`**，
禁止 `$(cat ...)` 这类嵌套 shell）、`node --check observer/web/*` 与直接跑 web 脚本
（**不用 `node -e`**）、`rg`、`ls observer/web*`；`git push` 一律 deny。
复合命令（`pwd` / `ps` / `lsof` 加管道拼在一起那种）匹配不上任何一条 allow，
结果是 `PermissionCancelled`，那**不是完成**，也**不是用户放弃**。
带宽泛授权的模式（`bypassPermissions` / `alwaysApprove` 之类）会被 `submit` 直接拒绝。

### 结局怎么判（**退出码 0 不等于完成**）

判据是四件事一起看：进程是不是真的结束了、日志有没有写完、有没有**唯一**的结果标记、
有没有权限取消 / 额度限制。任何一条对不上就给一个准确的状态，停在那里等人看，不忙着重试。

| `receipt_state` | 什么意思 |
|---|---|
| `cli_running` | 本调度启动的那个进程，身份核验过，还在跑 |
| `cli_observing` | 接管观察的既有进程：只读日志、只探测，**一个信号都不发** |
| `cli_exited_incomplete` | 进程没了，但日志最后一行是半条 —— 结果未知 |
| `cli_no_unique_result` | 退了、也没报错，但日志里没有唯一的 `CIV_RESULT_<任务>` |
| `permission_cancelled` | `stopReason=cancelled` / `PermissionCancelled`。**既不是完成，也不是"用户放弃了这场马拉松"** —— 只是某一次工具调用没被允许 |
| `quota_blocked` | 日志里明说额度/限流。不重试、不切付费通道 |
| `cli_failed` | 非零退出且没有结果标记 |
| `cli_user_cancelled` | 终态是人主动打断（graceful / user cancel）。不是失败也不是完成 |
| `cli_cancelled` | 终态说取消了，但没说是哪一种 |
| `cli_no_launch_record` | 认领落盘了，却没有 pid、没有匹配进程、日志也是空的 —— **说不清有没有启动过**，不当成死了 |
| `unknown` | 进程身份查不出来。不发信号、不下结论、不自动重跑 |
| `durable_ok` | 进程结束 + 日志完整 + 唯一结果标记。**也只进 `review`**，`done` 仍要外部带证据 `accept` |

### 日志格式（三种真实输出都要认）

归一化只有一个入口 `parse_journal()`，返回 `(记录, 有没有写完)`：

| 输出格式 | 长什么样 | 助手正文在哪 |
|---|---|---|
| `--output-format json` | **整份 stdout 就是一个缩进的 JSON 对象**（顶层 `text` / `stopReason` / `sessionId` / `requestId` / `usage` / …） | 顶层 `text` |
| NDJSON | 一行一条记录 | 记录里的 `text` |
| `--output-format streaming-json` | 一行一条，正文**逐片段**：`{"type":"text","data":"G"}`、下一条接着 `"CIV"`… | 按顺序拼起来的 `data` |
| ACP（原生 stream） | `agent_message_chunk` / `agent_thought_chunk` | `content.text`（thought 那条不算） |

踩过的坑：整份 pretty JSON 逐行 `json.loads` 一条都解析不出来，于是
"确认结束 + rc=0 + 真实 `end_turn` + 唯一标记"被判成 `cli_no_unique_result`。

- **找结果标记只看助手正文，而且原样拼接、一个换行都不加** —— streaming-json 的标记会跨片段，
  中间插东西就拆坏了。
- **整条排除**：`thought`（正文在 `data` 里，只删 `thought` 键没用）、`tool_call` /
  `tool_call_update` / `tool_result`、`available_commands`、`usage`、用户模板。
  私有思考与工具入参里出现的"结果标记"一律不算数，也**不会进 STATUS 或任何可读报告**。
- **半个对象不猜完成**：整份像个 JSON 对象却解析不了，或 NDJSON 里有解析不了的行，
  一律 `cli_exited_incomplete`（结果未知），哪怕标记本身已经写全了。
- 只有连 JSON 记录都解析不出来（根本不是 JSON 的输出格式）时，才退回搜索原始正文。

**终态记录的识别范围是写死的，没有臆造**：带顶层 `stopReason`、或 `type` 是
`result` / `turn_completed` 一类、或 `_meta` 里有 `cancellationCategory`。
streaming-json 的终态记录长什么样**尚未在官方 formatter 源码里核实过**；
认不出终态时不会假装有，而是在说明里写明"这一轮没有识别到终态记录，判定只靠唯一标记"。

**证据只从当前这一轮的终态记录里取。** 终态记录就是日志里最后一条带 `stopReason`、
或 `type` 是 `result` / `turn_completed` 的结构化记录（ACP 的 `cancellationCategory`
可能在 `_meta` 里）。两条硬规矩，都是踩过的坑：

1. **不扫助手正文。** 一句"未触发额度限制"不该被读成额度受限；测试名里的"额度"也一样。
   只看 `stopReason` / `cancellationCategory` / `error` 这类**表示结局**的字段。
2. **只认最后一条终态记录。** `--resume` 的日志里可能带着早先那一轮的失败或权限取消，
   那是历史。早先出过错、这一轮正常完成，结果就是正常完成。

**当前这一轮的终态取消/失败优先于此前出现过的标记**：一轮里先写了 `CIV_RESULT`、
随后被权限取消掉，那不是完成 —— 说明里会写清楚"标记出现过，但这一轮以取消收场"。

私有的 `thought` / `thinking` 字段**既不参与判定，也不进报告**。

退出码只有"**本进程这一趟启动的**"才拿得到（长期守护是这样）。一次性的 `tick`
起完进程就退了，子进程被 init 接管，退出码就是拿不到 —— 那时如实记 `null` 并在说明里写清楚，
判定改由日志承担，**不拿 0 当默认值**。

### 不重复派发 / 重启接管

- 认领**先落盘再启动**：`queue.json` 里先有 `cli_token`、命令数组与日志路径，才去起进程。
- 每次派工会把提示词原样复制到 `prompts/<token>.txt` 并用它当 `--prompt-file`，
  于是 token 出现在命令行里。守护重启后靠 `ps` 按 token 把那个进程**认回来**，
  而不是"没看到 pid 就再跑一遍"。扫不动进程表就记 `unknown`，仍然不重跑。
- 身份核验看的是**出生身份**（启动时刻 + 完整命令行），不是"我记得 pid 是多少"，
  **更不是"命令行里出现过那个 token"**。已经记下出生身份的，就严格逐字比对：
  启动时刻或命令行任何一处对不上，就是 pid 被复用 → `gone`，绝不对那个新进程发信号。
  `ps` 不可用 → `unknown`。
- **token 只用来找候选，不构成身份。** `cat /tmp/<token>.stdout.jsonl` 这种"在读我们
  同名文件"的进程也会被扫到；认领之前必须过一道**结构核对**：登记的那个 CLI 可执行文件
  确实出现在命令的字段里（带 shebang 的脚本前面会多出解释器，所以不要求它是 argv[0]），
  且 `--prompt-file` 的取值正是我们这次派工的提示词副本。两条都满足才认领。
  证实不了就是 `unknown` / 只观察，**绝不拿别的进程改写已经记下的 `cli_birth`**
  把它洗成自己的。已知限制：路径里带空格时按空白切分会失真，那时一律判"证实不了"
  （命令里**其它**参数带空格没关系，例如 `--allow Bash(git status*)`）。
- **扫到候选 ≠ 现在还是他。** 进程表扫完到真正认领之间，那个 pid 完全可能已经变成别的命令
  （实际观察到过：扫描时是 CLI，再读一次已经是 `tail`）。所以认领统一走一个共用的小函数
  `claim_candidate()`：**重新读一次**，先处理"读不到 / 读不了"，再拿**这一次读到的那一行**
  核身份，只有 match 才写 `cli_pid` / `cli_birth`。两个认领入口（`resolve_cli` 与
  `cli_reclaim`）共用它 —— 不再各写一份、各漏一处。候选失效时既不认领、不给信号权限，
  也不自动重派，继续按日志判"确实跑过并结束了"还是"根本没有启动痕迹"。
- **没有 pid 不等于进程死了。** 认领先落盘、再启动，中间有个崩溃窗口：token 已经写进队列、
  pid 还没写回来。那种情况会去扫进程表 + 看日志，分成三种结局：按 token 找到了 → 认回来；
  扫不动 → `unknown`（保持未知，下一轮再来）；确实没有进程、日志里却有输出 → 它确实跑过并
  结束了，按日志判结局；确实没有进程、日志也是空的 → `cli_no_launch_record`。
- 结局未定（`unknown` / `cli_no_launch_record` / 进程还活着）的 CLI 任务
  **既不放行同 owner 的返工，也不许再派新活**；`ps` 恢复正常之后，下一轮还能重新认领
  （`blocked` 的也认，否则会永远卡在未知上）。
- 同一个 owner 只要还有活着（或身份未确认）的 CLI 进程，就不派下一个。
- 同一个会话 + 同一份提示词还没验收完，`submit` 会直接拒绝：
  `--resume` 是**接着聊**，它不恢复代码快照，也不该被当成"再跑一次任务"。
  要不要在当前会话里继续修权限那一类事，留给主控决定。

### 暂停的边界（说实话的部分）

- **绝不经 Cockpit `reply_inject`**：headless CLI 没有安全的输入框。
- **不关任何借用的窗口/会话。**
- 默认的暂停只做一件事：**下一轮不再派**，并在任务上记一句话。
  当前这一轮**不会**被打断 —— 我们看不到它跑到哪一步，也做不到实时 checkpoint。
- 只有任务里显式写了 `"graceful_cancel": true` 才会发 CLI 官方的 SIGINT，
  且三个条件缺一不可：本调度启动的、**发信号前再核一次出生身份**、只发这一次。
  **永不 SIGKILL，日志一律保留。** 身份未知一律不发。
- 接管观察（`cli.adopt`）的进程**任何情况下都不发信号** —— 不知道是谁起的，就不动它。

## 任务 JSON 需要哪些字段

共同字段：`task_id`（大写下划线）、`owner`（`claude` / `grok`）、`objective`、
`allowed_paths`、`baseline_sha`、`dependencies`、`acceptance`、`workdir`、`branch`、
`prompt_file`。
Cockpit 通道另外要 `device_id`、`session_id`、`session_cwd`；
`transport: "grok-cli"` 要的是上一节那个 `cli` 对象；
可选 `rework_of`（指向同 owner 的 review/rejected/blocked 任务，用于受控返工）。
派工前会核对会话身份（source / cwd）与空闲边界，对不上就不投。

## 测试

```bash
python3 ops/test_dispatch.py      # 97 项，全部在临时目录里造假 hub / 假 CLI
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
轮次异常不杀守护也不丢队列、坏队列仍按原规则保留）、
`grok-cli` 通道（R22 组：显式命令数组与 `--resume`、新建会话不被叫成续用、
宽泛权限模式被拒、rc=0 但 `PermissionCancelled` 不算完成、rc=0 没有标记不算完成、
两个互相矛盾的标记算"没有唯一结果"、半条日志算未知、额度自成一类且不重试、
非零退出不算完成、自报只到 `review`、对象型 `tests` 不打爆摘要、
重复 `tick` 不重起进程、重启按 token 认回而不是重跑、pid 复用判 gone 且不发信号、
一个 owner 只跑一个、同会话同提示词被拒、暂停不注入也不发信号、
`graceful_cancel` 只打自己核验过的 pid、接管观察的进程一个信号都不发、
原生终端的 `[delivery state=unknown retry=none]` 判 unknown 而不是 failed）、
CLI 的三处边界（R23 组：token 落盘但没有 pid 时判未知而不是死亡、结局未定不放行返工、
没有启动痕迹自成一类、下一轮能重新认领、正文里提到"额度"不算额度受限、
终态里的真额度照样拦、私有 thought 不作证据也不进报告、
终态权限取消盖过此前的标记、只有 `stopReason=cancelled` 不算"没有唯一结果"、
用户打断与权限取消分开、历史里的失败不带进这一轮、ACP `_meta` 里的取消也认）、
身份核对（R24 组：同 token 但另一条命令/另一个启动时刻一律判 `gone` 且零信号、
出生身份逐字比对、缺出生信息时只认命令结构且容忍解释器前缀、
接管观察且无身份可比时判 `unknown`、`ps` 不可用时零信号、
认领拒绝 `cat`/`tail` 这类只读同名文件的候选、认领接受真正的 CLI 候选、
认领不改写已记录的出生身份、真实子进程核验身份后只发一次 SIGINT）、
候选确认（R25 组：扫到候选后二次读取变成 `tail` / 读不到 / 读不了 / 仍是同一个 CLI，
**两个认领入口跑同一份用例**，只有最后一种才认领，前三种零信号且不写错误的出生身份；
已记录的出生身份两个入口都洗不掉；认领身份的写入只允许存在于 `claim_candidate` 一处；
真实 Grok argv 里带空格的 `Bash(...)` / `Edit(...)` 规则不影响结构核对）、
日志格式（R26 组：真实的整份 pretty JSON 判成完成、私有思考不进 STATUS/报告、
截断的 pretty JSON 保持未知、streaming-json 分片原样拼接后标记成立、
`thought.data` 与工具入参里的假标记不算数、普通正文里的"额度"仍不误判、
真实终态取消仍然优先、ACP 与 NDJSON 两种老格式不受影响、
`parse_journal` 对"写没写完"的判断）。
`grok-cli` 那组用的是一个**假 CLI 脚本**，不联网、不碰真实 Grok 环境、
不接管任何正在跑的真实任务；发出去的信号只打测试自己起的子进程。

每条都验证过"把对应防护去掉就会红"：把这 35 项拿去跑 `aff0ed5` 会红 13 项，
跑 `3abe009` 会红 3 项（跨 chunk 的 tag、同 tick 两份返工、running 被返工插队），
跑 `4168356`（C04 之前）会红 15 项（3 failures + 12 errors），
跑 `dac9004`（C06 之前）R22 那 20 项**全红**，
跑 `59650b3`（C06_R1 之前）R23 那 13 项红 11 项，
跑 `046bf1c`（C06_R2 之前）R24 那 12 项红 9 项，
跑 `ac5fb43`（C06_R3 之前）R25 那 7 项红 6 项，
跑 `1fcaad8`（C06_R4 之前）R26 那 10 项红 8 项 —— 每一轮里此前各组都保持全绿，
说明没有回退任何已通过的边界。

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
- **做不到实时 checkpoint。** `grok-cli` 通道只能读它自己写出来的日志，
  进程跑到哪一步我们看不见。"在下一个安全点停下"= 下一轮不再派，不是把这一轮掐断。
- **不切付费通道、不改任何全局配置、不自动 bypass / always-approve。**
- 没有网络端口、没有远程命令入口。
- 不新建 Redis / 微服务 / Agent 平台，这个文件就是全部。
