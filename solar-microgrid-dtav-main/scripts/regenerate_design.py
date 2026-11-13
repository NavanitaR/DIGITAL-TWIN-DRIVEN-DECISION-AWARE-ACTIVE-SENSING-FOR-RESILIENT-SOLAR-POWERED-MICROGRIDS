"""Rebuild current design artifacts from canonical Markdown and hardware inputs.

Report dependencies: pip install -r scripts/requirements-docs.txt
Workbook needs the provided @oai/artifact-tool Node runtime. Set
ARTIFACT_TOOL_NODE_MODULES to its node_modules directory when not installed
in the repository's normal Node resolution path. --skip-workbook is an explicit
partial rebuild; do not use it after changing BOM inputs.
"""

from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--skip-workbook", action="store_true")
options = parser.parse_args()
env = os.environ.copy()
candidate = (
    Path.home()
    / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
if (
    "ARTIFACT_TOOL_NODE_MODULES" not in env
    and (candidate / "@oai/artifact-tool").exists()
):
    env["ARTIFACT_TOOL_NODE_MODULES"] = str(candidate)


def run(*args):
    subprocess.run(args, cwd=ROOT, env=env, check=True)


for script in [
    "generate_hardware.py",
    "wiring_details.py",
    "generate_diagrams.py",
    "generate_docs.py",
]:
    run(sys.executable, str(ROOT / "scripts" / script))
if not options.skip_workbook:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node is required to regenerate BOM.xlsx")
    run(node, str(ROOT / "scripts/build_bom.mjs"))
else:
    print("Explicit partial rebuild: BOM.xlsx was not regenerated")
run(sys.executable, str(ROOT / "scripts/build_report.py"))
run(sys.executable, str(ROOT / "scripts/build_report.py"), "--guide")
run(sys.executable, str(ROOT / "scripts/check_artifacts.py"))
print("Current design artifacts regenerated; physical commissioning remains separate")
