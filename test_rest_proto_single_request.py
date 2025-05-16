#!/usr/bin/env python3
"""
Benchmark suite for the REST-protobuf implementation.

* 1, 10, 1 000, 10 000, 100 000 and 1 000 000 records
* 50 repetitions each
* Separate log pair (server / client) for every record count
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from contextlib import suppress

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

HOST         = "127.0.0.1"
PORT         = "8000"
ITERATIONS   = 50
SIZES        = (1, 10)

LOG_DIR      = Path("data/single_request")
SERVER_FILE  = "rest_proto_server/server.py"
CLIENT_FILE  = "rest_proto_server/single_request_client.py"

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def start_server(count: int) -> subprocess.Popen:
    server_log = LOG_DIR / f"rest-server-{count}-items.jsonl"

    cmd = [
        sys.executable,
        SERVER_FILE,
        "--host", HOST,
        "--port", PORT,
        "--pool-size", str(count),
        "--logger-name", f"rest-server-{count}",
        "--log-file", str(server_log),
    ]
    # stdout is silenced so the parent process controls console output
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)


def run_client(count: int) -> int:
    client_log = LOG_DIR / f"rest-client-{count}-items.jsonl"

    cmd = [
        sys.executable,
        CLIENT_FILE,
        "--host", HOST,
        "--port", PORT,
        "--count", str(count),
        "--logger-name", f"rest-client-{count}",
        "--log-file", str(client_log),
    ]
    return subprocess.run(cmd).returncode


def stop_server(proc: subprocess.Popen) -> None:
    proc.send_signal(signal.SIGINT)
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=5)
    if proc.poll() is None:
        proc.kill()


# --------------------------------------------------------------------------- #
# Main loop                                                                   #
# --------------------------------------------------------------------------- #

def main() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    for size in SIZES:
        print(f"\n=== {size:_} items · {ITERATIONS} runs ===")

        # 1. Start server ---------------------------------------------------
        print("🔧  Starting REST + Proto server …")
        server_proc = start_server(size)
        time.sleep(10)                     # give it a moment to bind

        try:
            # 2. Fire client ------------------------------------------------
            for i in range(1, ITERATIONS + 1):
                print(f"  📥  Run {i:3d}/{ITERATIONS} … ", end="", flush=True)
                rc = run_client(size)
                if rc:
                    print(f"⚠️  client exit={rc}")
                    break
                print("✅")
        finally:
            # 3. Clean shutdown --------------------------------------------
            print("🛑  Shutting down server …")
            stop_server(server_proc)

    print("\n🏁  All benchmarks finished.")
    print("\n🏁  Pausing to relieve pressure on memory")
    time.sleep(10)


if __name__ == "__main__":
    main()
