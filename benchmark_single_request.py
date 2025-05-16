#!/usr/bin/env python3
"""
Unified benchmark runner for gRPC-Proto, REST-Proto and REST-JSON.

Usage examples
--------------
# run with default configs
python bench.py grpc
python bench.py rest_proto
python bench.py rest_json

# override some knobs
python bench.py rest_json --sizes 1 10 1000 --iterations 20
"""

import argparse
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path

# --------------------------------------------------------------------------- #
# Per-variant static configuration                                             #
# --------------------------------------------------------------------------- #

LOG_DIR = "data/single_request"
HOST = "127.0.0.1"

DEFAULT_ITERATION = 50
DEFAULT_SIZES = [1, 10]
DEFAULT_PAUSE_SECONDS = 10

CFG = {
    "grpc": {
        "server_file":  "grpc_server/server.py",
        "client_file":  "grpc_server/single_request_client.py",
        "port": 50051,
        "logger_prefix": "grpc",
    },
    "rest_proto": {
        "server_file":  "rest_proto_server/server.py",
        "client_file":  "rest_proto_server/single_request_client.py",
        "port": 8000,
        "logger_prefix": "rest_proto",
    },
    "rest_json": {
        "server_file":  "rest_json_server/server.py",
        "client_file":  "rest_json_server/single_request_client.py",
        "port": 8001,
        "logger_prefix": "rest_json",
    },
}


def start_server(mode: str, count: int) -> subprocess.Popen:
    cfg = CFG[mode]
    server_log = LOG_DIR / f"server-{count}-items.jsonl"

    cmd = [
        sys.executable, cfg["server_file"],
        "--host", HOST,
        "--port", cfg["port"],
        "--pool-size", str(count),
        "--logger-name", f"{cfg['logger_prefix']}-server-{count}",
        "--log-file", str(server_log),
    ]
    # silence server stdout / stderr
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)


def run_client(mode: str, count: int) -> int:
    cfg = CFG[mode]
    client_log = LOG_DIR / f"client-{count}-items.jsonl"

    cmd = [
        sys.executable, cfg["client_file"],
        "--host", HOST,
        "--port", cfg["port"],
        "--count", str(count),
        "--logger-name", f"{cfg['logger_prefix']}-client-{count}",
        "--log-file", str(client_log),
    ]
    return subprocess.run(cmd).returncode


def stop_server(proc: subprocess.Popen) -> None:
    proc.send_signal(signal.SIGINT)
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=5)
    if proc.poll() is None:
        proc.kill()


def main() -> None:
    ap = argparse.ArgumentParser(description="Unified single request latency benchmark")
    ap.add_argument("mode", choices=CFG.keys(),
                    help="Which stack to benchmark")
    ap.add_argument("--iterations", type=int, default=DEFAULT_ITERATION)
    ap.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES,
                    help="Record counts to request")
    ap.add_argument("--pause", type=int, default=DEFAULT_PAUSE_SECONDS,
                    help="Seconds to wait for server start / final cool-off")

    args = ap.parse_args()

    log_dir = Path(f"{LOG_DIR}/{args.mode}")
    log_dir.mkdir(parents=True, exist_ok=True)

    for size in args.sizes:
        print(f"\n=== {size:_} items · {args.iterations} runs "
              f"({args.mode}) ===")

        print(f"🔧  Starting {args.mode} server …")
        server_proc = start_server(args.mode, size)
        time.sleep(args.pause)

        try:
            for i in range(1, args.iterations + 1):
                print(f"  📥  Run {i:3d}/{args.iterations} … ", end="", flush=True)
                rc = run_client(args.mode, size)
                if rc:
                    print(f"⚠️  client exit={rc}")
                    break
                print("✅")
        finally:
            print("🛑  Shutting down server …")
            stop_server(server_proc)
            print(f"\n🏁  Pausing {args.pause}s to relieve pressure on memory")
            time.sleep(args.pause)

    print("\n🏁  All benchmarks finished.")


if __name__ == "__main__":
    main()
