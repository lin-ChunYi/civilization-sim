# 连续开发进度

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
