# 连续开发进度

反馈版本：GROK-REVIEW.md（G04 三项 + G05 四项 + G07 两项；C08 未到）。本检查点已修这些项。

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
- C08 EXP01/02 仍未在 config，未冒充
- tests：g09-qa-cdp 10/10；g09-create-cdp 6/6

# 连续开发进度（历史）

## G09 旅程复审
- t1 116/6/0；t4 18→10；t52 split 无格；t83-aid-3 6457；t124 回助 kcal 1011984 / changed 0；t125 share 格 0
- 导出无令牌；URL 可恢复
- tests：g09-journey-cdp 9/9
- C08 EXP01/02 仍未交付，未空等

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
