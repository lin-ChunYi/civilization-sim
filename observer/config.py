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

# 模拟引擎。都是只读加载，绝不修改。默认引擎仍是 exp03，不把 01/02 当 03 的归零。
#   exp01：采集/消耗/储存/局部迁移（冻结 20da486）
#   exp02：资源再生年际波动（冻结 c5a1f18）；SIGMA_M=0 时退化复现 EXP-01
#   exp03：迁移死亡代价（冻结基线）
#   exp04–06：信息交换 / 援助 / 优先回助
ENGINES = {
    "exp01": {"path": REPO_ROOT / "exp01" / "verify.py",
              "baseline_commit": "20da486",
              "label": "EXP-01 采集 / 消耗 / 储存 / 局部迁移",
              "params": []},
    "exp02": {"path": REPO_ROOT / "exp02" / "verify2.py",
              "baseline_commit": "c5a1f18",
              "label": "EXP-02 资源再生的年际波动",
              "params": ["sigma_m"]},
    "exp03": {"path": REPO_ROOT / "exp03" / "verify3.py",
              "baseline_commit": "6b6af4f",
              "label": "EXP-03 迁移死亡代价（冻结基线）",
              "params": ["sigma_m", "move_mort_m"]},
    "exp04": {"path": REPO_ROOT / "exp04" / "verify4.py",
              "baseline_commit": "68015cc（已审阅）",
              "label": "EXP-04 同格信息交换",
              "params": ["sigma_m", "move_mort_m", "share_m"]},
    "exp05": {"path": REPO_ROOT / "exp05" / "verify5.py",
              "baseline_commit": "d20a015（已实现待审）",
              "label": "EXP-05 同格食物援助",
              "params": ["sigma_m", "move_mort_m", "share_m", "aid_m"]},
    "exp06": {"path": REPO_ROOT / "exp06" / "verify6.py",
              "baseline_commit": "本轮实现（待审）",
              "label": "EXP-06 援助记忆与优先回助",
              "params": ["sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m"]},
    "exp07": {"path": REPO_ROOT / "exp07" / "verify7.py",
              "baseline_commit": "本轮实现（待审）",
              "label": "EXP-07 原始耕作与弃耕",
              "params": ["sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m",
                         "farm_m"]},
}
DEFAULT_ENGINE = "exp03"

# 每个参数的能力说明：范围、默认值、单位、一句话含义。
# **由后台提供，前端按能力展示**，不用每加一个 EXP 就猜一次。
# 范围的权威来源是引擎里的常量，这里只写展示信息；adapter 会用引擎常量覆盖 min/max。
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
# 用户按下取消之后，留给工作进程"算完这一年自己停"的协作窗口。
# 超过这个秒数还在跑，说明它卡在某一步里读不到取消标志，才会去停止它。
# **只有用户明确取消才起算**；没有取消请求时，这个值不参与任何判断。
CANCEL_GRACE_SEC = float(os.environ.get("OBSERVER_CANCEL_GRACE", "15"))

# API 契约版本。新增字段递增小版本；删改字段必须先改契约文档再动代码。
# 本批（C_CONT_01）新增续演接口，属于**新增字段/新增端点**，小版本递增到 obs-1.9。
# 旧记录里存着的 api_version 保留它自己的历史身份，不回头改写。
# 本批（EXP-07）新增 farm 段与 farm_m 参数，属于新增，小版本递增到 obs-1.10。
# 旧记录里存着的 api_version 保留它自己的历史身份，不回头改写。
# 本批（ANIME-WATCH-01）新增只读端点 GET /api/runs/{id}/watch-plan，属于新增端点，
# 小版本递增到 obs-1.11。既有端点的语义一个字没改。
API_VERSION = "obs-1.11"

# --- 续演（C_CONT_01）---
# 只有**新建的 EXP-06 运行**才会写检查点；旧运行与预生成案例没有检查点，
# 也就没有续演资格 —— 不自动补跑，不拿最后一年的画面冒充检查点。
# EXP-06 与 EXP-07 各自**同版本**续演：EXP-06 的存档只能续成 EXP-06，
# 不会被无声升级成农业世界（引擎身份与记录器 schema 两道都拦着）。
CONTINUATION_ENGINES = ("exp06", "exp07")
MAX_ADDITIONAL_YEARS = 300          # 一次续演最多新增多少年
MIN_ADDITIONAL_YEARS = 1
# 累计世界年上限。**这是上限，不是"已经标定到 3000 年"**：本轮实测到 600 年。
MAX_WORLD_YEAR = int(os.environ.get("OBSERVER_MAX_WORLD_YEAR", "3000"))
CHECKPOINT_NAME = "checkpoint.json"

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


PARAM_SPECS = {
    "sigma_m": {"label": "资源再生年际波动", "unit": "‰（千分之一）",
                "min": 0, "max": 1000, "default": 0,
                "note": "0 = 无波动（退化为 EXP-01）。不是气候模型，是受控的资源扰动源。"},
    "move_mort_m": {"label": "迁移死亡强度", "unit": "‰（千分之一）",
                    "min": 0, "max": 1000, "default": 0,
                    "note": "代价作用于人口而不是储存，适用于所有迁移，不是只罚误判。"},
    "share_m": {"label": "同格信息交换的参与概率", "unit": "‰（千分之一）",
                "min": 0, "max": 1000, "default": 0,
                "note": "每个群体每年抽一次签；0 = 不交换。"},
    "aid_m": {"label": "供给方愿意拿出的可援助余粮比例", "unit": "‰（千分之一）",
              "min": 0, "max": 1000, "default": 0,
              "note": "**不是参与概率**。先保留自己当年的需求，超出部分按这个比例作为预算。"},
    "recip_m": {"label": "优先回助的预算比例", "unit": "‰（千分之一）",
                "min": 0, "max": 1000, "default": 0,
                "note": "预算中优先分给'以前帮过我、现在同格且缺粮'的群体的比例；"
                        "没用掉的回到普通援助。0 = 不做优先回助。"},
    "farm_m": {"label": "投到耕作上的折算劳动比例", "unit": "‰（千分之一）",
               "min": 0, "max": 1000, "default": 0,
               "note": "人口 N 对应 N×1000 个折算劳动刻度，这一比例投到耕作、其余去采集。"
                       "**这是人口折算预算，不是说每个婴儿都在劳动**；0 = 不耕作。"},
    "seed": {"label": "随机种子", "unit": "整数", "min": 0, "max": MAX_SEED, "default": 0,
             "note": "同种子同参数逐位可复现。"},
    "years": {"label": "模拟年数", "unit": "年", "min": 1, "max": MAX_YEARS, "default": 120,
              "note": "服务端上限见 limits.max_years。"},
}
