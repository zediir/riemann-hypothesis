"""Workflow-owned stock releases and independently validated cache baselines."""
import argparse
import json
from pathlib import Path
import re
from types import SimpleNamespace

CONFIG = json.loads(Path(__file__).with_name("cache-baselines.json").read_text())
if CONFIG.get("schema") != 1 or CONFIG.get("active_toolchain") not in CONFIG.get("toolchains", {}):
    raise ValueError("invalid trusted cache baseline configuration")


def for_toolchain(toolchain):
    if toolchain not in ("leanprover/lean4:v4.33.1", "leanprover/lean4:v4.36.0", "leanprover/lean4:v4.37.0-rc1"):
        raise ValueError("cache configuration requires an approved stock toolchain")
    entry = CONFIG["toolchains"][toolchain]
    baseline = entry["baseline"]
    values = dict(TOOLCHAIN=toolchain, TOOLCHAIN_DIR=toolchain.replace("/", "--").replace(":", "---"),
                  VERSION=toolchain.split(":v", 1)[1], COMMIT=entry["commit"],
                  DEPENDENCIES=entry["dependency_manifest_sha256"], BASELINE=baseline,
                  REVISION=baseline["revision"] if baseline else None,
                  MAP_SHA=baseline["map_sha256"] if baseline else None,
                  MANIFEST_SHA=baseline["manifest_sha256"] if baseline else None)
    if not re.fullmatch(r"[0-9a-f]{40}", values["COMMIT"]):
        raise ValueError("invalid stock toolchain commit pin")
    if values["DEPENDENCIES"] is not None and not re.fullmatch(r"[0-9a-f]{64}", values["DEPENDENCIES"]):
        raise ValueError("invalid dependency manifest pin")
    if baseline and (not re.fullmatch(r"[0-9a-f]{40}", values["REVISION"]) or
                     not all(re.fullmatch(r"[0-9a-f]{64}", values[key]) for key in ("MAP_SHA", "MANIFEST_SHA"))):
        raise ValueError("invalid completed baseline pins")
    return SimpleNamespace(**values)


globals().update(vars(for_toolchain(CONFIG["active_toolchain"])))


def require_baseline():
    if not BASELINE or DEPENDENCIES is None:
        raise ValueError(f"no completed, validated public cache baseline is configured for {TOOLCHAIN}")
    return BASELINE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, help="validated workflow identity of an already completed build")
    args = parser.parse_args()
    print(for_toolchain(json.loads(args.expected.read_text())["toolchain"]).TOOLCHAIN if args.expected else TOOLCHAIN)
