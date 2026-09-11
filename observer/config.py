"""OBS-01 观察台配置。全部可用环境变量覆盖，默认值面向单用户本地使用。"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVER_DIR = REPO_ROOT / "observer"

# 数据目录：SQLite + 每次运行的逐年记录。线上部署时挂到持久盘。
DATA_DIR = Path(os.environ.get("OBSERVER_DATA_DIR", OBSERVER_DIR / "data")).resolve()
DB_PATH = DATA_DIR / "observer.db"
RUNS_DIR = DATA_DIR / "runs"

# 网页目录。**observer/web/ 由 UI 分支（Grok）负责，后台不写入这里。**
# 测试需要挂别的目录时用 OBSERVER_WEB_DIR 覆盖，不要往 web/ 里丢临时文件。
WEB_DIR = Path(os.environ.get("OBSERVER_WEB_DIR", OBSERVER_DIR / "web")).resolve()
# 后台自己的浏览器回归用页面，挂在 /selftest，与前端目录彻底分开。
SELFTEST_DIR = Path(os.environ.get("OBSERVER_SELFTEST_DIR",
                                   OBSERVER_DIR / "tests" / "web")).resolve()

# 模拟引擎。都是只读加载，绝不修改。
#   exp03：已冻结的基线（迁移死亡代价）
#   exp04：同格信息交换（已获批准实现，待审）
ENGINES = {
    "exp03": {"path": REPO_ROOT / "exp03" / "verify3.py",
              "baseline_commit": "6b6af4f",
              "label": "EXP-03 迁移死亡代价（冻结基线）",
              "params": ["sigma_m", "move_mort_m"]},
    "exp04": {"path": REPO_ROOT / "exp04" / "verify4.py",
              "baseline_commit": "本轮实现（待审）",
              "label": "EXP-04 同格信息交换",
              "params": ["sigma_m", "move_mort_m", "share_m"]},
}
DEFAULT_ENGINE = "exp03"
# 兼容旧代码的别名
ENGINE_PATH = ENGINES[DEFAULT_ENGINE]["path"]
ENGINE_BASELINE_COMMIT = ENGINES[DEFAULT_ENGINE]["baseline_commit"]

# --- 服务端硬上限（不依赖前端控件）---
MAX_YEARS = int(os.environ.get("OBSERVER_MAX_YEARS", "300"))       # 单次运行年数上限
MIN_YEARS = 1
MAX_RUNS = int(os.environ.get("OBSERVER_MAX_RUNS", "50"))          # 可保存的运行条数
MAX_DATA_MB = int(os.environ.get("OBSERVER_MAX_DATA_MB", "512"))   # 数据目录总量上限
MAX_SEED = 2**31 - 1
WRITE_RATE_LIMIT = int(os.environ.get("OBSERVER_WRITE_RATE", "12"))  # 每 IP 每分钟写请求数
# 占了槽却迟迟没有工作进程接手：超过这个秒数就判定进程没起来，回收任务槽。
QUEUE_GRACE_SEC = float(os.environ.get("OBSERVER_QUEUE_GRACE", "20"))

# API 契约版本。新增字段递增小版本；删改字段必须先改契约文档再动代码。
API_VERSION = "obs-1.2"

# --- 访问保护 ---
# 设了 OBSERVER_TOKEN：所有 /api 请求都要带令牌（服务端校验，前端不硬编码）。
# 没设：只读接口开放，写接口仅允许来自本机 —— 本地单用户模式。
TOKEN = os.environ.get("OBSERVER_TOKEN", "").strip()
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}

ARMS = {
    "memory": {"poison": "", "label": "记忆臂（默认）",
               "note": "群体只知道自己去过或侦察过的格；没去过的邻格是 UNKNOWN。"},
    "omniscient": {"poison": "omniscient", "label": "全知对照臂",
                   "note": "EXP-03 的信息上界对照臂（引擎里的 omniscient 语义开关），"
                           "迁移决策直接读当年真值。它是对照臂，不是一个新的世界机制。"},
}
