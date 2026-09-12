# 连续开发进度

## GROK_BUILD_008 检查点
- O28m：预置无消失时用隔离短记录承重「消失前年卷宗仍写活着」，run_tests **214/0/0 未覆盖**。
- 03 八方向接到迁徙行路（`data-face`，不是新群体）。walk-c/d 加入近似走姿组，仍不宣称可循环。
- 试玩仍按用户要求先放：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
- tests：run_tests 214/0/0；game-v2-unit 24/0；game-v2-cdp 21/0（V3 face=nw）
- 8765/8772 未动。

## GROK_BUILD_007 检查点
- 闭环本波剩余：390 选中卡片改为贴在播放条上方，不再叠住播放；采集者选中/给予用 15 状态图；选中环改为描边椭圆（原 PNG 内孔是实心白底）。
- 03 八方向是另一套斗篷人物，不混进六名群体代表。行走仍是两帧近似姿势 + 程序摆动，不是已验证循环。
- 试玩：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
- tests：run_tests 213/0/1uncov（O28m）；c07 16/0；c08 51/0；game-v2-unit 22/0；game-v2-cdp 21/0（V8 sheetAbove mapH=384 dockH=84）；engines-cdp 7/0；c08-wizard 6/0；g04-fix 6/0；g05 11/0；g06 5/0；g07 5/0；director-logic 18/0
- 本波后停下。Codex 尚未试玩。8765/8772 未动。

## GROK_BUILD_006 检查点
- ART-PACK-001 选 variant-01，去底/裁切/对齐写入 `observer/web/assets/sprites/`（源目录只读）。未把白底 JPG 整张贴上地图。
- 人物/地块/头像已接入；援助/信息用 pair 图锚事件格；迁移两帧近似走姿+程序摆动（不是已验证循环）；创世页用 menu-bg；随身包袱只作装饰。
- PLAYTEST-001 布局保留：桌面/390 地图与播放同屏，选中卡片+回沙盘，事件条在地图顶。
- 试玩：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
  建议 t=0 看人物与地块；点人物看头像卡片；t=4 迁移；t=83 援助；t=125 信息；创世页看菜单插画。
- tests：game-v2-unit 21/0；game-v2-cdp 21/0（V1 data-art=sprite hexArt=64 无白底JPG；V0b 桌面 dock 788–837 mapH=503；V8 390 mapH=489 dockIn chipH=26）；director-logic 18/0；g04-fix 6/0
- 本波完成后按用户指令停下，不等 Codex 试玩，不开始下一轮优化。
- 8765/8772 仍 obs-1.7，未动。

## GROK_BUILD_005 检查点
- 素材包尚未落到 observer/web/assets，未空等、未生图。
- 390：隐藏概览卡，地图高度约 489px；卷宗浮层上限 28vh 且可再点「卷宗」关闭；格子侧裙加高、顶边高光、赭石/苔绿资源色、营地改等距菱形、深棕轮廓。
- 试玩：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
  建议 390 首屏直接播放；第 4 年迁移看端点动作。
- tests：game-v2-unit 21/0；game-v2-cdp 21/0（V8 mapH=489 dockIn）；g04-fix 6/0；director-logic 18/0
- 下一轮：接入 Codex 等距素材清单；8765/8772 仍 obs-1.7。

## GROK_BUILD_004 检查点
- PLAYTEST-001：播放条贴沙盘底部，桌面/390 首屏同时看见地图与播放；选中群体卡片+回沙盘；事件条改到地图顶部且变矮；镜头平移限幅。
- 手机卷宗改为底部浮层，不把播放钮顶出视口。口径收到「来源与口径」。手机提示改为拖动/+−。
- 未等待 Imagine 素材包。
- 试玩：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
  建议首屏点播放；390 点人物看卡片/回沙盘；事件模式第 4、12 年迁移。
- tests：game-v2-unit 21/0；game-v2-cdp 21/0（V0b 播放条、V2b 卡片、V8 390 chipH=26 dockIn mapH=346）；g04-fix 6/0；director-logic 18/0
- 下一轮：接入手绘等距素材（裁切去底）；浮层卷宗再收；8765/8772 仍 obs-1.7。

## GROK_BUILD_003 检查点
- 从 7152f60 续：默认缩放下拉开四种体型（staff / stocky / cloak / scout），营地更大、名字更早出现、点选热区 44×50。
- 事件播放：事件间隔 1600ms、行走 1100ms，字幕 11px 描边；分裂只在沙盘顶栏写「地点未记录 · 不在地图上猜测」，不猜格。
- 390 宽：时间轴按钮 ≥44px，事件行 min-height 44px。
- 8788 PID 8659 未重启（静态即当前 web）。8765/8772 未动。
- 试玩：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
  建议 t=0 看营地体型 → 点选 → 事件模式 t=4 迁移 / t=83 援助 / t=125 信息 / t=52 分裂。
- tests：game-v2-unit 20/0；game-v2-cdp 19/0（silN=3 cloak/scout/staff）；director-logic 18/0；g04-fix 6/0
- 下一轮：事件模式手机卷宗与沙盘联动更醒目；衣饰对比再加强；bitmap 精灵仍可选；Safari 无 headless。

## GROK_BUILD_002 检查点
- 从 a217dc42 续：先跑完整 `observer/run_tests.py`，修 O18b/O18c（毒化脚本删行导致语法错，自检 dump 0 条 FAIL）。
- 毒化现同时关掉 opAlive / yearNavAlive / openRun 世代守卫，且不再用正则删行。套件 **213 pass / 0 fail / 1 uncovered**（O28m 预置无消失，未覆盖）。
- 游戏品质：群体代表改为 1–3 人营地（按人口分档）、营地底盘、选中旗帜与镜头跟过去；六边形加装饰性侧裙增加层次（不是地形事实）；迁移动作分离开/移动/到达；HUD「动效开/关」。
- 8788 已用显式 `OBSERVER_BUILD_COMMIT=a217dc42…` 重启，数据 `/tmp/obs-g2-8788` 保留。8765/8772 未杀。
- 入口：http://127.0.0.1:8788/static/index.html#tab=world&run=preset-exp06-recip1000&t=0
- tests：run_tests 213/0/1uncov；c07 16/0；c08 51/0；game-v2-unit 19/0；game-v2-cdp 19/0（8788，营地/侧裙/阶段/390）；c08-wizard 6/0；g04-fix 6/0；g05 11/0；g06 5/0；g07 5/0；director-logic 18/0
- Safari 有安装但无可用 headless CDP；Firefox 未安装。
- 下一轮：人物体量与衣饰再拉开；播放节奏/事件聚焦更清楚；手机点选命中；可选 bitmap 精灵；不要空等浏览器。

## game-v2 + C07/C08 检查点（上轮）
- 标准：GROK-REVIEW.md `standard_version: game-v2`。G03 导演 659b726 不重做。
- 世界主画面保留沙盘。圆点/菱形棋子换成 **SVG 群体代表**（头/衣/绶带/道具，稳定配色，待机/选中）。明确不是独立个人。
- 动作：迁移只演示记录的 from→to 端点（直线插值 + 端点圈，不编中间格子）；share/aid/repay 锚 `e.cell`；split/extinct 不定位。
- 播放/暂停/速度仍有效；减少动效时迁移停在终点姿态。
- C07：启动时冻结 `service_identity`；显式构建标识优先；无 git 为 unknown。
- C08：config 登记 exp01–exp06；缺账本省略不填 0；不支持参数非 0 拒绝；默认仍 exp03。
- 交接：Claude 未提交的 adapter/app/config 已完成可运行检查点并写入本仓库；之后不再改这批后端文件，除非契约再变。
- 稳定 8765/8772 **未重启**（obs-1.7）。本机隔离服务 `127.0.0.1:8788` 为 obs-1.8 + 当前 UI。
- tests：
  - game-v2-unit-test 16/0
  - game-v2-cdp 19/0（8772 长局 946a58d28b05，真鼠标选中、迁移/信息/援助/分裂、390、减少动效）
  - game-v2-engines-cdp 7/0（8788 六引擎向导、EXP01 未记录、键盘、hash）
  - c07_version_test 16/0；c08_engines_test 51/0；c08-wizard-test 6/0
  - 回归：director-logic 18/0、g03-r2-nav 12/0、g03-race 12/0、g04-fix 6/0、g04-relations 14/0、g05-compare 11/0、g06-wizard 5/0、g07-lib 5/0
  - 8788 实建 exp01–exp06 各 4 年并回放 year/0 与 year/4
- 截图：`observer/web/screenshots/game-v2/`

## G04 返工
- 边卡绑定 run|year|scope，换年/换run清空
- jumpToRecordedEvent 捕获 run/op，stale 不跨 run
- 双向曲线控制点分离；文字标签与边旋钮可真实鼠标点
- 表用群体名称为主，id 次级字符串
- tests：g04-fix-test 6/6；g04-fix-cdp 8/8 真鼠标
- next：旅程 QA 已跑

## QA 旅程
- 向导：非法年数拒绝；预设 AID+RECIP 1000；确认可取消
- 真实新建 exp03–06 各 5 年运行（确认摘要与 engine 一致）
- 收藏隔离、对照缺失、2.5s@8x 回到第 30 年、390 HUD 52px extra=0
- HTML 检索未注入
- C08 EXP01/02 当时未在已部署 config；现已在源码 obs-1.8 与 8788 接入（见上节）
- tests：g09-qa-cdp 10/10；g09-create-cdp 6/6

# 连续开发进度（历史）

## G09 旅程复审
- t1 116/6/0；t4 18→10；t52 split 无格；t83-aid-3 6457；t124 回助 kcal 1011984 / changed 0；t125 share 格 0
- 导出无令牌；URL 可恢复
- tests：g09-journey-cdp 9/9
- C08 EXP01/02 本轮已接入源码（见文首检查点），当时未空等

## G08 窄屏 HUD
- 375px HUD 52px（原约 247）；四次跳年实测约 13ms，不编 FPS
- tests：g08-cdp 4/4

## G07 书签 / 收藏 / 检索 / 导出
- localStorage 按 run 隔离；导出白名单无令牌/私人路径
- tests：g07-lib-test 4/4
- next：G08 窄屏 HUD 与实测

## G06 创世向导
- 预设无援助/仅援助/援助+优先回助；recip>0 且 AID=0 警告且不暗改
- 确认摘要后才 POST；EXP01/02 待 C08
- tests：g06-wizard-test 5/5
- next：G07 书签收藏检索导出

## G05 双世界同年对照
- 缺年标缺失，不夹终年；recip_m 差异如实列出
- tests：g05-compare-test 6/6；g05-cdp 4/4
- next：G06 创世向导

## G04 按年档案 / 关系网
- commit：见本阶段 git
- `/band?at_year` 与 `/relations?at_year` 默认不含未来；全档案需点「全档案」
- 关系网圆布局，不是地图；有向边分开；普通/优先/回助分列；recip.changed 在诊断
- 节点进档案，边事件可跳 t83-aid-3
- tests：g04-relations-test.mjs 14/14；g04-cdp.mjs 9/9
- next：G05 双世界同年对照

## 依赖
- 后端 C08 EXP01/02 未交付，任务 1 暂缓
- C07 版本身份随后
