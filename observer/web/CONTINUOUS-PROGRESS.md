# 连续开发进度

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
