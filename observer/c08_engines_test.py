"""C08：六引擎登记、EXP-01/02 原始哈希、缺指标不填 0、不支持参数拒绝。"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
TEST_DATA = Path(tempfile.mkdtemp(prefix="obs-c08-"))
os.environ["OBSERVER_DATA_DIR"] = str(TEST_DATA)
os.environ.setdefault("OBSERVER_WRITE_RATE", "500")

from fastapi.testclient import TestClient  # noqa: E402

from observer import adapter, config  # noqa: E402
from observer.app import app  # noqa: E402

RESULTS = []


def record(name, state, detail=""):
    RESULTS.append((name, state, detail))
    mark = {"PASS": "PASS", "FAIL": "FAIL"}[state]
    print("  " + name + "  " + mark + (("  " + detail) if detail else ""))


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def wait_done(client, run_id, timeout=90):
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        r = client.get("/api/runs/" + run_id)
        if r.status_code != 200:
            return {"status": "http-" + str(r.status_code), "body": r.text[:200]}
        last = r.json()
        if last.get("status") in ("done", "failed", "interrupted", "canceled"):
            return last
        time.sleep(0.15)
    return last or {"status": "timeout"}


def sample_hashes(engine, sigma_m=0, move_mort_m=0, arm="memory"):
    st = adapter.make_world(31337, sigma_m, move_mort_m, arm, engine=engine)
    rec = adapter.Recorder(engine)
    out = {}
    out[0] = rec.year_record(st)
    for t in range(1, 5):
        adapter.step(st, engine)
        row = rec.year_record(st)
        if t in (1, 4):
            out[t] = row
    return out, st


print("=" * 72)
print("C08 six engines")
print("=" * 72)

check("C08-01 default engine remains exp03", config.DEFAULT_ENGINE == "exp03",
      config.DEFAULT_ENGINE)
check("C08-02 engines registered",
      list(config.ENGINES) == ["exp01", "exp02", "exp03", "exp04", "exp05", "exp06",
                               "exp07"],
      str(list(config.ENGINES)))
check("C08-03 api_version obs-1.11", config.API_VERSION == "obs-1.11", config.API_VERSION)
check("C08-04 exp01 params empty", config.ENGINES["exp01"]["params"] == [])
check("C08-05 exp02 params sigma only", config.ENGINES["exp02"]["params"] == ["sigma_m"])

i1 = adapter.engine_info("exp01")
i2 = adapter.engine_info("exp02")
check("C08-06 exp01 sha256",
      i1["engine_sha256"] == "46305aef4b975d68f295c54cbe0287cd7f0b1aad5a02cef515eb8ea953f65534",
      i1["engine_sha256"][:16])
check("C08-07 exp02 sha256",
      i2["engine_sha256"] == "31444a6c545c1cb686a4a04f87d4c1daca59e3e618490ce9b896cdff25e4566a",
      i2["engine_sha256"][:16])
check("C08-08 exp01 unsupported includes sigma/mort",
      "sigma_m" in i1["unsupported_params"] and "move_mort_m" in i1["unsupported_params"])
check("C08-09 exp01 no population_identity metric",
      i1["metrics"]["population_identity"] is False)
check("C08-10 exp02 has sigma not mort",
      i2["metrics"]["sigma"] is True and i2["metrics"]["move_mort"] is False)

h01, st01 = sample_hashes("exp01")
check("C08-11 exp01 t0 hash",
      h01[0]["integrity"]["state_hash"] == "5d9bc934deff6e3c166a6973de86d532"
      and h01[0]["agg"]["pop"] == 120, h01[0]["integrity"]["state_hash"])
check("C08-12 exp01 t1 hash",
      h01[1]["integrity"]["state_hash"] == "0fb0ad1af763589bab6c10e223001a24"
      and h01[1]["agg"]["pop"] == 116, h01[1]["integrity"]["state_hash"])
check("C08-13 exp01 t4 hash",
      h01[4]["integrity"]["state_hash"] == "32d66979f87999581f60f4d4ab8ffc3b"
      and h01[4]["agg"]["pop"] == 122, h01[4]["integrity"]["state_hash"])

missing = ("births_cum", "deaths_demo_cum", "mig_deaths_cum", "need_cum",
           "personyear_cum", "deficit_cum")
check("C08-14 exp01 omits population ledger",
      all(k not in h01[1]["cum"] and k not in h01[1]["year"] for k in missing),
      str(sorted(h01[1]["cum"])))
check("C08-15 exp01 bands omit macc",
      all("macc" not in b for b in h01[0]["bands"]))
check("C08-16 exp01 omits population_identity_error",
      "population_identity_error" not in h01[0]["integrity"])
st01_t0 = adapter.make_world(31337, 0, 0, "memory", engine="exp01")
meta01 = adapter.static_run_meta(st01_t0)
check("C08-17 exp01 pop_start is summed not engine field",
      meta01["pop_start"] == 120 and "no pop_start field" in meta01["pop_start_note"]
      and st01_t0.get("tick", 0) == 0,
      meta01["pop_start_note"] + " pop=" + str(meta01["pop_start"]))

h02, _st02 = sample_hashes("exp02", sigma_m=0)
check("C08-18 exp02 sigma0 t0",
      h02[0]["integrity"]["state_hash"] == "db967861903d9235c8cea2de7ad1da66",
      h02[0]["integrity"]["state_hash"])
check("C08-19 exp02 sigma0 t1",
      h02[1]["integrity"]["state_hash"] == "0c9c938797c81494bb5953637895a974")
check("C08-20 exp02 sigma0 t4",
      h02[4]["integrity"]["state_hash"] == "72f2db787cf672e95f1441f6527477d4")
check("C08-21 exp02 != exp01 (not impersonation)",
      h02[0]["integrity"]["state_hash"] != h01[0]["integrity"]["state_hash"])

h02s, _ = sample_hashes("exp02", sigma_m=1000)
check("C08-22 exp02 sigma1000 actually changes state",
      h02s[0]["integrity"]["state_hash"] == "dbd77afb933aa031953a6da45706d0c4"
      and h02s[1]["integrity"]["state_hash"] == "ef0bfd3da3eac86197da5ded959092df"
      and h02s[4]["integrity"]["state_hash"] == "7e7878302cd2b29b7d2927891e0efc37",
      h02s[4]["integrity"]["state_hash"])
check("C08-23 exp02 has deficit_cum not births_cum",
      "deficit_cum" in h02[1]["cum"] and "births_cum" not in h02[1]["cum"])

st_plain = adapter.make_world(31337, 0, 0, "memory", engine="exp01")
v1, _ = adapter.load_engine("exp01")
plain = [v1.state_hash(st_plain)]
for _ in range(4):
    v1.step(st_plain)
    plain.append(v1.state_hash(st_plain))
st_rec = adapter.make_world(31337, 0, 0, "memory", engine="exp01")
rr = adapter.Recorder("exp01")
rec_h = [rr.year_record(st_rec)["integrity"]["state_hash"]]
for _ in range(4):
    adapter.step(st_rec, "exp01")
    rec_h.append(rr.year_record(st_rec)["integrity"]["state_hash"])
check("C08-24 recorder does not perturb exp01", rec_h == plain, str(rec_h))

h03, _ = sample_hashes("exp03", sigma_m=0, move_mort_m=0)
check("C08-25 exp03 zeros not equal exp01",
      h03[0]["integrity"]["state_hash"] != h01[0]["integrity"]["state_hash"])

client = TestClient(app)
created = {}
with client:
    cfg = client.get("/api/config").json()
    check("C08-26 config lists six engines",
          set(cfg.get("engines", {})) == set(config.ENGINES),
          str(sorted(cfg.get("engines", {}))))
    check("C08-27 config default exp03", cfg.get("default_engine") == "exp03")
    r = client.post("/api/runs", json={"seed": 31337, "years": 4, "engine": "exp01",
                                       "sigma_m": 400, "arm": "memory", "label": "bad-sigma"})
    check("C08-28 exp01 nonzero sigma rejected", r.status_code == 400, str(r.json())[:80])
    r = client.post("/api/runs", json={"seed": 31337, "years": 4, "engine": "exp01",
                                       "move_mort_m": 50, "arm": "memory", "label": "bad-mort"})
    check("C08-29 exp01 nonzero mort rejected", r.status_code == 400, str(r.json())[:80])
    r = client.post("/api/runs", json={"seed": 31337, "years": 4, "engine": "exp02",
                                       "move_mort_m": 1, "arm": "memory", "label": "bad-mort2"})
    check("C08-30 exp02 nonzero mort rejected", r.status_code == 400, str(r.json())[:80])

    bodies = {
        "exp01": {"seed": 31337, "years": 4, "engine": "exp01", "arm": "memory",
                  "label": "c08-exp01"},
        "exp02": {"seed": 31337, "years": 4, "engine": "exp02", "sigma_m": 0, "arm": "memory",
                  "label": "c08-exp02"},
        "exp03": {"seed": 31337, "years": 4, "engine": "exp03", "sigma_m": 0,
                  "move_mort_m": 0, "arm": "memory", "label": "c08-exp03"},
        "exp04": {"seed": 31337, "years": 4, "engine": "exp04", "sigma_m": 0,
                  "move_mort_m": 0, "share_m": 0, "arm": "memory", "label": "c08-exp04"},
        "exp05": {"seed": 31337, "years": 4, "engine": "exp05", "sigma_m": 0,
                  "move_mort_m": 0, "share_m": 0, "aid_m": 0, "arm": "memory",
                  "label": "c08-exp05"},
        "exp06": {"seed": 31337, "years": 4, "engine": "exp06", "sigma_m": 0,
                  "move_mort_m": 0, "share_m": 0, "aid_m": 0, "recip_m": 0, "arm": "memory",
                  "label": "c08-exp06"},
    }
    for name, body in bodies.items():
        r = client.post("/api/runs", json=body)
        ok_post = r.status_code == 200
        run_id = r.json().get("run_id") if ok_post else None
        check("C08-create-" + name, ok_post, str(r.json())[:80])
        if not run_id:
            continue
        done = wait_done(client, run_id)
        check("C08-done-" + name, done.get("status") == "done" and done.get("engine") == name,
              json.dumps({"status": done.get("status"), "engine": done.get("engine"),
                          "error": (done.get("error") or "")[:80]}))
        created[name] = run_id
        y0 = client.get("/api/runs/" + run_id + "/year/0")
        y1 = client.get("/api/runs/" + run_id + "/year/1")
        y4 = client.get("/api/runs/" + run_id + "/year/4")
        check("C08-replay-" + name,
              y0.status_code == 200 and y1.status_code == 200 and y4.status_code == 200,
              str(y0.status_code) + "/" + str(y1.status_code) + "/" + str(y4.status_code))
        if name == "exp01" and y0.status_code == 200 and y4.status_code == 200:
            a, b = y0.json(), y4.json()
            check("C08-api-exp01-hash",
                  a["integrity"]["state_hash"] == "5d9bc934deff6e3c166a6973de86d532"
                  and b["integrity"]["state_hash"] == "32d66979f87999581f60f4d4ab8ffc3b"
                  and "births_cum" not in a.get("cum", {})
                  and "population_identity_error" not in a.get("integrity", {}))
            rel = client.get("/api/runs/" + run_id + "/relations?at_year=4")
            d = rel.json() if rel.status_code == 200 else {}
            check("C08-exp01-relations-empty-capability",
                  rel.status_code == 200 and d.get("totals", {}).get("edges") == 0
                  and d.get("engine_supports", {}).get("aid") is False,
                  str(d.get("engine_supports")))
        if name == "exp02" and y0.status_code == 200 and y4.status_code == 200:
            a, b = y0.json(), y4.json()
            check("C08-api-exp02-hash",
                  a["integrity"]["state_hash"] == "db967861903d9235c8cea2de7ad1da66"
                  and b["integrity"]["state_hash"] == "72f2db787cf672e95f1441f6527477d4")

npass = sum(1 for _, s, _ in RESULTS if s == "PASS")
nfail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
print("=" * 72)
print("pass=" + str(npass) + " fail=" + str(nfail) + " created=" + json.dumps(created))
shutil.rmtree(TEST_DATA, ignore_errors=True)
sys.exit(1 if nfail else 0)
