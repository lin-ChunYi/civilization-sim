"""C07：服务身份在启动时固定；显式构建标识优先；无 Git 为 unknown；不泄露路径/令牌。"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
TEST_DATA = Path(tempfile.mkdtemp(prefix="obs-c07-"))
os.environ["OBSERVER_DATA_DIR"] = str(TEST_DATA)
os.environ.pop("OBSERVER_BUILD_COMMIT", None)
os.environ.pop("OBSERVER_UI_BUILD", None)

from fastapi.testclient import TestClient  # noqa: E402

from observer import app as obs_app  # noqa: E402

RESULTS = []


def record(name, state, detail=""):
    RESULTS.append((name, state, detail))
    mark = {"PASS": "PASS", "FAIL": "FAIL"}[state]
    print("  " + name + "  " + mark + (("  " + detail) if detail else ""))


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


print("=" * 72)
print("C07 service identity")
print("=" * 72)

frozen = dict(obs_app.SERVICE_IDENTITY)
check("C07-01 identity frozen at import",
      frozen.get("repo_commit") and frozen.get("repo_commit_source") in
      ("git_startup", "explicit_build", "unknown"),
      json.dumps({k: frozen.get(k) for k in ("repo_commit", "repo_commit_source", "api_version")}))

orig_git = obs_app._git_head
obs_app._git_head = lambda: "ffffffffffffffffffffffffffffffffffffffff"
try:
    still = obs_app.repo_commit()
    ident_now = obs_app.SERVICE_IDENTITY["repo_commit"]
    check("C07-02 HEAD change after start does not move frozen identity",
          ident_now == frozen["repo_commit"] and still == obs_app.repo_commit(),
          "frozen=" + str(frozen["repo_commit"])[:12] + " live_git_would=" + orig_git()[:12]
          if callable(orig_git) else "ok")
    live = obs_app._service_identity()
    check("C07-03 re-read would see new git (proves freeze is necessary)",
          live.get("repo_commit") == "ffffffffffffffffffffffffffffffffffffffff"
          and live.get("repo_commit_source") == "git_startup")
finally:
    obs_app._git_head = orig_git

os.environ["OBSERVER_BUILD_COMMIT"] = "accepted-archive-abc123"
os.environ["OBSERVER_UI_BUILD"] = "ui-label-not-a-browser-hash"
try:
    exp = obs_app._service_identity()
    check("C07-04 explicit build wins",
          exp["repo_commit"] == "accepted-archive-abc123"
          and exp["repo_commit_source"] == "explicit_build",
          json.dumps(exp))
    check("C07-05 ui_build is optional label not browser hash",
          exp["ui_build"] == "ui-label-not-a-browser-hash"
          and "not a hash of bytes currently loaded in the browser" in (exp.get("ui_build_note") or ""))
finally:
    os.environ.pop("OBSERVER_BUILD_COMMIT", None)
    os.environ.pop("OBSERVER_UI_BUILD", None)

obs_app._git_head = lambda: ""
try:
    unk = obs_app._service_identity()
    check("C07-06 no git is unknown not guessed",
          unk["repo_commit"] == "unknown" and unk["repo_commit_source"] == "unknown",
          json.dumps(unk))
finally:
    obs_app._git_head = orig_git

client = TestClient(obs_app.app)
with client:
    cfg = client.get("/api/config").json()
    blob = json.dumps(cfg)
    si = cfg.get("service_identity") or {}
    check("C07-07 config exposes service_identity",
          si.get("repo_commit") == frozen["repo_commit"]
          and si.get("repo_commit_source") == frozen["repo_commit_source"]
          and si.get("api_version") == frozen["api_version"],
          json.dumps(si))
    check("C07-08 old repo_commit field still present", "repo_commit" in cfg)
    check("C07-09 no token or absolute private paths",
          "OBSERVER_TOKEN" not in blob and "/Users/" not in blob
          and "app_secret" not in blob.lower()
          and not str((cfg.get("engine") or {}).get("engine_path") or "").startswith("/"),
          str((cfg.get("engine") or {}).get("engine_path")))
    check("C07-10 does not claim disk web hash is loaded UI",
          "currently loaded in the browser" in (si.get("ui_build_note") or ""))
    for name, info in (cfg.get("engines") or {}).items():
        path = info.get("engine_path") or ""
        check("C07-path-" + name, path.startswith("exp") and "/" in path and not path.startswith("/"),
              path)

npass = sum(1 for _, s, _ in RESULTS if s == "PASS")
nfail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
print("=" * 72)
print("pass=" + str(npass) + " fail=" + str(nfail))
shutil.rmtree(TEST_DATA, ignore_errors=True)
sys.exit(1 if nfail else 0)
