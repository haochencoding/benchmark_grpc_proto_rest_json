#!/usr/bin/env python3
"""
pid_monitor.py  –  sample CPU and memory of a running process

Usage
-----
python pid_monitor.py <PID> <out_file.jsonl> [--interval 0.2]

Records one JSON line per sample:
{"ts": 1715965234.115274, "rss": 73424896, "cpu": 37.5}

* ts   : seconds since epoch (time.time()).
* rss  : resident set size in bytes.
* cpu  : percent CPU since last sample (same meaning as psutil.cpu_percent()).
"""

import argparse
import json
import time
import psutil

DEFAULT_SAMPLING_INTERVAL = 0.002


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("outfile")
    ap.add_argument("--interval", type=float, default=DEFAULT_SAMPLING_INTERVAL,
                    help=f"sampling interval in seconds (default: {DEFAULT_SAMPLING_INTERVAL})")
    args = ap.parse_args()

    proc = psutil.Process(args.pid)
    with open(args.outfile, "w") as fh:
        # prime the cpu_percent() logic
        proc.cpu_percent(None)

        while proc.is_running():
            try:
                ts   = time.time()
                rss  = proc.memory_info().rss
                cpu  = proc.cpu_percent(None)   # % since last call
                fh.write(json.dumps({"ts": ts, "rss": rss, "cpu": cpu}) + "\n")
                fh.flush()
                time.sleep(args.interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break


if __name__ == "__main__":
    main()
