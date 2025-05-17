#!/usr/bin/env python3
"""
main.py
-------
Launch one or more benchmark-runner scripts in sequence.

Example: No arguments → run default runners
python main.py

Example: With arguments → runs each script you list, in that order
python main.py run_benchmark_single_request.py run_benchmark_single_request.py
"""

import subprocess
import sys
from pathlib import Path

DEFAULT_RUNNERS = ["run_benchmark_single_request.py", "convert_jsonl_to_csv.py"]


def main() -> None:
    scripts = sys.argv[1:] or DEFAULT_RUNNERS

    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            sys.exit(f"❌  '{script}' not found")

        print(f"\n🚀  Running {script_path} ...")
        rc = subprocess.call([sys.executable, str(script_path)])
        if rc:
            sys.exit(f"❌  '{script}' exited with code {rc}")

    print("\n🏁  All scripts finished successfully.")


if __name__ == "__main__":
    main()
