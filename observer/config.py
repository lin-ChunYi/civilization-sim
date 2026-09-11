"""OBS-01 观察台配置。全部可用环境变量覆盖，默认值面向单用户本地使用。"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVER_DIR = REPO_ROOT / "observer"

# 数据目录：SQLite + 每次运行的逐年记录。线上部署时挂到持久盘。
DATA_DIR = Path(os.environ.get("OBSERVER_DATA_DIR", OBSERVER_DIR / "data")).resolve()
DB_PATH = DATA_DIR / "observer.db"
RUNS_DIR = DATA_DIR / "runs"

# 模拟引擎：已冻结的 EXP-03 基线，只读加载，绝不修改。
ENGINE_PATH = REPO_ROOT / "exp03" / "verify3.py"
ENGINE_BASELINE_COMMIT = "6b6af4f"

# --- 服务端硬上限（不依赖前端控件）---
MAX_YEARS = int(os.environ.get("OBSERVER_MAX_YEARS", "300"))       # 单次运行年数上限
MIN_YEARS = 1
MAX_RUNS = int(os.environ.get("OBSERVER_MAX_RUNS", "50"))          # 可保存的运行条数
MAX_DATA_MB = int(os.environ.get("OBSERVER_MAX_DATA_MB", "512"))   # 数据目录总量上限
MAX_SEED = 2**31 - 1
WRITE_RATE_LIMIT = int(os.environ.get("OBSERVER_WRITE_RATE", "12"))  # 每 IP 每分钟写请求数

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
