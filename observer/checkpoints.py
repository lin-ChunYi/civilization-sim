"""检查点：把一次运行在某个完整年度边界上的**全部**状态安全地存下来，以便续演。

这份文件只做四件事：**安全编码 / 解码 / 校验 / 原子保存**。它不决定谁有资格续演
（那是 `continuation.py`），也不跑模型。

几条不肯让步的规矩：

* **不用 pickle、不 eval、不从上传的文件里还原对象。** 只认一种显式带类型标记的 JSON。
* **不"猜"键的类型。** `json.loads` 会把 `{1: x}` 的键变成 `"1"`，猜回去迟早猜错。
  所以字典一律编码成 `[[键, 值], ...]` 的条目表，整数键就是整数键。
* **重复键、不认识的类型、超深、超大，一律拒绝**，不做"尽力而为"的容错。
* 世界状态是全整数的：**遇到浮点直接拒绝**。浮点混进状态本身就是 EXP-01 起的红线。
* 完整性摘要只用来发现损坏，**不是鉴权**。检查点只从服务自己的数据目录读，
  不提供任意路径读取，也没有外部存档上传入口。
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Tuple

CHECKPOINT_SCHEMA = "obs-checkpoint-v1"
RECORDER_SCHEMA = "obs-recorder-v1"

MAX_DEPTH = 64                      # 编码/解码的最大嵌套深度
MAX_BYTES = 64 * 1024 * 1024        # 单个检查点文件的上限
_TAG = "~t"                         # 类型标记键；普通 dict 不会用到它


class CheckpointError(ValueError):
    """检查点不可信：格式、类型、完整性或身份对不上。**一律拒绝，不做部分恢复。**"""


def _check_key(k: Any, _depth: int = 0) -> None:
    """字典键只允许：整数、字符串，或者由它们组成的元组。

    元组键是真实存在的：记录器里 `_aid_by_pair` 的键就是 (供给方, 接收方)。
    布尔要单独挡掉（它是 int 的子类，`{True: x}` 与 `{1: x}` 会撞在一起）。
    """
    if _depth > MAX_DEPTH:
        raise CheckpointError("字典键嵌套过深")
    if isinstance(k, bool):
        raise CheckpointError("字典键不允许布尔值（它和整数会撞键）")
    if isinstance(k, (int, str)):
        return
    if isinstance(k, tuple):
        for part in k:
            _check_key(part, _depth + 1)
        return
    raise CheckpointError("字典键只允许整数 / 字符串 / 它们组成的元组，收到 %r" % (k,))


# ---------------------------------------------------------------- 编码

def encode(value: Any, _depth: int = 0) -> Any:
    """把模型状态编码成可 JSON 化的结构，**类型显式标记**。"""
    if _depth > MAX_DEPTH:
        raise CheckpointError("状态嵌套超过 %d 层，拒绝编码" % MAX_DEPTH)
    if value is None or isinstance(value, (bool, str)):
        return value                      # bool 必须在 int 之前判：它是 int 的子类
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise CheckpointError("世界状态里出现浮点数（%r）——这是红线，不编码" % value)
    if isinstance(value, list):
        return [encode(v, _depth + 1) for v in value]
    if isinstance(value, tuple):
        return {_TAG: "tuple", "v": [encode(v, _depth + 1) for v in value]}
    if isinstance(value, dict):
        items = []
        seen = set()
        for k, v in value.items():
            _check_key(k)
            mark = (type(k).__name__, k)
            if mark in seen:
                raise CheckpointError("字典里出现重复键 %r" % (k,))
            seen.add(mark)
            items.append([encode(k, _depth + 1), encode(v, _depth + 1)])
        return {_TAG: "dict", "v": items}
    raise CheckpointError("不支持的类型 %s" % type(value).__name__)


def _pairs_hook(pairs):
    """`json.loads` 默认把重复键**静默**取最后一个。这里直接拒绝。"""
    out = {}
    for k, v in pairs:
        if k in out:
            raise CheckpointError("JSON 对象里出现重复键 %r" % (k,))
        out[k] = v
    return out


def decode(node: Any, _depth: int = 0) -> Any:
    """解码。遇到任何不认识的结构就抛 CheckpointError，不猜、不跳过。"""
    if _depth > MAX_DEPTH:
        raise CheckpointError("解码深度超过 %d 层，拒绝" % MAX_DEPTH)
    if node is None or isinstance(node, (bool, int, str)):
        return node
    if isinstance(node, float):
        raise CheckpointError("检查点里出现浮点数，拒绝")
    if isinstance(node, list):
        return [decode(v, _depth + 1) for v in node]
    if isinstance(node, dict):
        tag = node.get(_TAG)
        if tag not in ("dict", "tuple") or set(node) != {_TAG, "v"}:
            raise CheckpointError("不认识的编码节点：%s" % sorted(node)[:4])
        body = node["v"]
        if not isinstance(body, list):
            raise CheckpointError("编码节点的 v 必须是数组")
        if tag == "tuple":
            return tuple(decode(v, _depth + 1) for v in body)
        out = {}
        for item in body:
            if not isinstance(item, list) or len(item) != 2:
                raise CheckpointError("字典条目必须是 [键, 值]")
            k = decode(item[0], _depth + 1)
            _check_key(k)
            if k in out:
                raise CheckpointError("解码时发现重复字典键 %r" % (k,))
            out[k] = decode(item[1], _depth + 1)
        return out
    raise CheckpointError("不认识的节点类型 %s" % type(node).__name__)


# ---------------------------------------------------------------- 组装与校验

def _canon(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def build(*, engine: str, engine_sha256: str, engine_path: str, params: Dict[str, Any],
          params_fingerprint: str, model_run_id: str, tick: int, full_digest: str,
          state_hash: str, model_state: Any, recorder_state: Any,
          history_bytes: int, history_records: int, history_sha256: str) -> Dict[str, Any]:
    """组装一个检查点负载，并算出整份负载的完整性摘要。"""
    payload = {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "recorder_schema": RECORDER_SCHEMA,
        "engine": engine,
        "engine_sha256": engine_sha256,
        "engine_path": engine_path,
        "params": dict(params),
        "params_fingerprint": params_fingerprint,
        "model_run_id": model_run_id,
        "tick": int(tick),
        "full_digest": full_digest,
        "state_hash": state_hash,
        "model_state": encode(model_state),
        "recorder_state": encode(recorder_state),
        "history": {"bytes": int(history_bytes), "records": int(history_records),
                    "sha256": history_sha256},
        "written_at": time.time(),
    }
    return {"payload": payload, "digest": hashlib.sha256(_canon(payload)).hexdigest()}


def save(path: Path, doc: Dict[str, Any]) -> None:
    """原子保存：临时文件 -> flush -> fsync -> os.replace。权限 0600。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise CheckpointError("检查点 %d 字节，超过上限 %d" % (len(raw), MAX_BYTES))
    with tmp.open("wb") as fh:
        fh.write(raw)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load(path: Path) -> Dict[str, Any]:
    """读并**完整校验**一个检查点。任何一处对不上都抛 CheckpointError。"""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise CheckpointError("读不到检查点：%s" % exc)
    if size > MAX_BYTES:
        raise CheckpointError("检查点 %d 字节，超过上限 %d" % (size, MAX_BYTES))
    try:
        raw = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CheckpointError("检查点读不出来：%s" % exc)
    try:
        doc = json.loads(raw, object_pairs_hook=_pairs_hook)
    except CheckpointError:
        raise
    except ValueError as exc:
        raise CheckpointError("检查点不是合法 JSON：%s" % exc)
    if not isinstance(doc, dict) or set(doc) != {"payload", "digest"}:
        raise CheckpointError("检查点外层结构不对")
    payload = doc["payload"]
    if not isinstance(payload, dict):
        raise CheckpointError("检查点 payload 不是对象")
    if hashlib.sha256(_canon(payload)).hexdigest() != doc["digest"]:
        raise CheckpointError("检查点完整性摘要对不上（文件已损坏或被改过）")
    if payload.get("checkpoint_schema") != CHECKPOINT_SCHEMA:
        raise CheckpointError("检查点格式版本不认识：%r" % payload.get("checkpoint_schema"))
    if payload.get("recorder_schema") != RECORDER_SCHEMA:
        raise CheckpointError("记录器格式版本不认识：%r" % payload.get("recorder_schema"))
    for key in ("engine", "engine_sha256", "engine_path", "params_fingerprint",
                "model_run_id", "full_digest", "state_hash"):
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise CheckpointError("检查点缺字段或类型不对：%s" % key)
    if not isinstance(payload.get("tick"), int) or isinstance(payload.get("tick"), bool):
        raise CheckpointError("检查点的 tick 必须是整数")
    hist = payload.get("history")
    if not isinstance(hist, dict) or not isinstance(hist.get("bytes"), int) \
            or not isinstance(hist.get("records"), int) \
            or not isinstance(hist.get("sha256"), str):
        raise CheckpointError("检查点的 history 段不完整")
    return payload


def restore(payload: Dict[str, Any]) -> Tuple[Any, Any]:
    """把校验过的负载解成 (模型状态, 记录器状态)。"""
    return decode(payload["model_state"]), decode(payload["recorder_state"])


def prefix_sha256(path: Path, nbytes: int) -> str:
    """历史文件**前 nbytes 字节**的 sha256。半条尾记录天然被排除在外。"""
    h = hashlib.sha256()
    left = nbytes
    with path.open("rb") as fh:
        while left > 0:
            chunk = fh.read(min(1 << 20, left))
            if not chunk:
                raise CheckpointError("历史文件比检查点记的还短")
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()
