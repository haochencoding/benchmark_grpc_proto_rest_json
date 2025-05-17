#!/usr/bin/env python3
"""
Unified benchmark runner for gRPC-Proto, REST-Proto and REST-JSON.

Usage examples
--------------
# run with default configs
python benchmark_single_request.py grpc
python benchmark_single_request.py rest_proto
python benchmark_single_request.py rest_json

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
import socket
from utils.timeline_anchor import write_timeline_anchor
# --------------------------------------------------------------------------- #
# Per-variant static configuration                                            #
# --------------------------------------------------------------------------- #

LOG_DIR = "data/single_request"
HOST = "127.0.0.1"

DEFAULT_ITERATION = 100
DEFAULT_SIZES = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]
DEFAULT_PAUSE_SECONDS = 30

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


def wait_for_port(mode: str, timeout: float = 30.0, interval: float = 0.1):
    """
    Block until a TCP socket at (host, port) accepts connections, or
    raise TimeoutError after timeout seconds.
    """
    port = CFG[mode]["port"]
    deadline = time.time() + timeout
    while True:
        try:
            with socket.create_connection((HOST, port), timeout=interval):
                return
        except OSError:
            if time.time() > deadline:
                raise TimeoutError(f"Timed out waiting for {HOST}:{port}")
            time.sleep(interval)


def start_server(mode: str, count: int) -> subprocess.Popen:
    cfg = CFG[mode]
    server_log = f"{LOG_DIR}/{mode}/server-{count}-items.jsonl"

    cmd = [
        sys.executable, cfg["server_file"],
        "--host", HOST,
        "--port", str(cfg["port"]),
        "--pool-size", str(count),
        "--logger-name", f"{cfg['logger_prefix']}-server-{count}",
        "--log-file", str(server_log),
    ]
    # silence server stdout / stderr
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)


def run_client(mode: str, count: int) -> int:
    cfg = CFG[mode]
    client_log = f"{LOG_DIR}/{mode}/client-{count}-items.jsonl"
    client_monitoring_log = f"{LOG_DIR}/{mode}/usage-client-{count}-items.jsonl"

    cmd = [
        sys.executable, cfg["client_file"],
        "--host", HOST,
        "--port", str(cfg["port"]),
        "--count", str(count),
        "--logger-name", f"{cfg['logger_prefix']}-client-{count}",
        "--log-file", str(client_log),
    ]

    # spawn client + monitor
    proc = subprocess.Popen(cmd)
    monitoring_proc = subprocess.Popen(
        [sys.executable, "pid_monitor.py", str(proc.pid), client_monitoring_log],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )

    rc = proc.wait()
    monitoring_proc.terminate()
    monitoring_proc.wait()
    return rc


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

        # Add a timeanchor to convert perf_base_ns to normal timestamp
        write_timeline_anchor(f"{log_dir}/time_anchor.jsonl", mode=args.mode, size=size)

        server_proc = start_server(args.mode, size)

        monitoring_log = f"{log_dir}/usage-server-{size}-items.jsonl"
        monitoring_proc = subprocess.Popen(
            [sys.executable, "pid_monitor.py", str(server_proc.pid), str(monitoring_log)],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )

        wait_for_port(args.mode)

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
            monitoring_proc.terminate()
            monitoring_proc.wait()
            print(f"\n🏁  Pausing {args.pause}s before starting the next server")
            time.sleep(args.pause)

    print("\n🏁  All benchmarks finished.")


if __name__ == "__main__":
    main()
