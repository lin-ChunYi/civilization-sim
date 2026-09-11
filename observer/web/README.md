# 观察台前端（UI 分支）

本目录归 UI 分支。后台只读、不往这里写文件。接口以
[`docs/OBS-01-API-CONTRACT.md`](../../docs/OBS-01-API-CONTRACT.md) 为准。

启动方式不变：在仓库根目录

```bash
python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8765
```

打开 http://127.0.0.1:8765 即世界概览。旧地址 `#tab=events` 会跳到概览里的事件区。

前端自检（不改模拟结果）：http://127.0.0.1:8765/static/overview-selftest.html  
后台那套请求串扰回归仍在 http://127.0.0.1:8765/selftest/selftest.html

口径：

- 「正在查看」是回放年；「计算进度」是后台已经算到哪。二者分开。
- 人口、群体、累计事件、本年摘要都跟随回放年。
- 第 0 年显示「开局」，不伪造同比。
- 事件条数来自已记录清单，不是出生人数，也不拿账本迁移次数去凑。
- 不含 LLM 生成的历史。
