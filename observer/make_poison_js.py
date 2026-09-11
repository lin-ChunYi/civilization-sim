"""生成前端“注入版”脚本：把修复前的两个毛病放回去，用来验证自检真的会红。

  1. 年份缓存退回“只按 t 作键”，并去掉所有“迟到响应”的守卫；
  2. 转义函数退化成恒等。

只在测试时生成到 observer/web/_poison_selftest.js，跑完即删，不进版本库。
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent / "web" / "app.js"
DST = Path(__file__).resolve().parent / "web" / "_poison_selftest.js"


def build() -> Path:
    s = SRC.read_text(encoding="utf-8")
    s = s.replace("const stale = (myEpoch, myRun) =>\n"
                  "  S.epoch !== myEpoch || !S.run || S.run.run_id !== myRun;",
                  "const stale = () => false;   // 注入：取消“迟到响应”守卫")
    s = s.replace("const ykey = (runId, t) => `${runId}|${t}`;",
                  "const ykey = (runId, t) => String(t);   // 注入：缓存退回只按 t 作键")
    s = re.sub(r"^.*S\.epoch !== myEpoch.*\n", "", s, flags=re.M)      # openRun 里的守卫
    s = re.sub(r"^.*stale\(myEpoch, myRun\).*\n", "", s, flags=re.M)   # 其余守卫
    s = s.replace("function esc(x) {\n  return String",
                  "function esc(x) {\n  return String(x);   // 注入：不转义\n  return String")
    DST.write_text(s, encoding="utf-8")
    return DST


if __name__ == "__main__":
    print(build())
