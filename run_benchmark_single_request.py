#!/usr/bin/env python3
"""
Run `benchmark_single_request.py` three times in a row:

    1. grpc
    2. rest_proto
    3. rest_json

A pause separates the runs.
Any extra CLI flags are forwarded to the benchmark script unchanged.
"""

import subprocess
import sys
import time

BENCH = "benchmark_single_request.py"
MODES = ["grpc", "rest_proto", "rest_json"]
PAUSE = 30                                 # seconds


def main() -> None:
    passthrough = sys.argv[1:]             # forward everything

    for i, mode in enumerate(MODES, 1):
        print(f"\n🚀  [{i}/3] Running {mode} benchmark …\n")
        rc = subprocess.run(
            [sys.executable, BENCH, mode] + passthrough,
            check=False
        ).returncode
        if rc:
            sys.exit(f"❌  {mode} benchmark failed with code {rc}")

        if i < len(MODES):                 # skip pause after last run
            print(f"\n⏸️   Waiting {PAUSE} s before next mode …")
            time.sleep(PAUSE)

    print("\n🏁  All three benchmarks finished successfully.")


if __name__ == "__main__":
    main()
