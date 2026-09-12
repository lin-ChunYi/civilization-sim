"""生成前端“注入版”脚本：把修复前的两个毛病放回去，用来验证自检真的会红。

  1. 年份缓存退回“只按 t 作键”，并去掉所有“迟到响应”的守卫；
  2. 转义函数退化成恒等。

**只读** observer/web/app.js（那是 UI 分支的文件），产物写到 observer/tests/web/_poison_app.js，
跑完即删，不进版本库。后台绝不往 observer/web/ 里写东西。
"""
from pathlib import Path

from . import config

SRC = config.WEB_DIR / "app.js"
DST = config.SELFTEST_DIR / "_poison_app.js"


def build() -> Path:
    DST.parent.mkdir(parents=True, exist_ok=True)
    s = SRC.read_text(encoding="utf-8")
    s = s.replace("const stale = (myEpoch, myRun) =>\n"
                  "  S.epoch !== myEpoch || !S.run || S.run.run_id !== myRun;",
                  "const stale = () => false;   // 注入：取消“迟到响应”守卫")
    s = s.replace("const ykey = (runId, t) => `${runId}|${t}`;",
                  "const ykey = (runId, t) => String(t);   // 注入：缓存退回只按 t 作键")
    s = s.replace("function opAlive(op) {\n  return op === S.opGen;\n}",
                  "function opAlive(op) { return true; }")
    s = s.replace("function yearNavAlive(myEpoch, myRun, myOp) {\n"
                  "  return opAlive(myOp) && !stale(myEpoch, myRun);\n}",
                  "function yearNavAlive(myEpoch, myRun, myOp) { return true; }")
    s = s.replace("if (S.epoch !== myEpoch || !opAlive(myOp)) return { ok: false, reason: \"stale\" };",
                  "if (false) return { ok: false, reason: \"stale\" };")
    s = s.replace("function bandAccept(epoch, runId, bandId, scope, year, req) {\n"
                  "  if (stale(epoch, runId)) return false;",
                  "function bandAccept(epoch, runId, bandId, scope, year, req) {\n"
                  "  return true; if (stale(epoch, runId)) return false;")
    s = s.replace("function esc(x) {\n  return String",
                  "function esc(x) {\n  return String(x);   // 注入：不转义\n  return String")
    DST.write_text(s, encoding="utf-8")
    return DST


if __name__ == "__main__":
    print(build())
