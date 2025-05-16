#!/usr/bin/env python3
"""
Run one-shot gRPC benchmarks:

* 1, 10, 1 000, 10 000, 100 000 and 1 000 000 records
* 100 repetitions each
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
PORT         = "50051"
ITERATIONS   = 50                                   # how many calls per size
SIZES        = (100_000, 1_000_000)

LOG_DIR      = Path("data/single_request")
SERVER_FILE  = "grpc_server/server.py"
CLIENT_FILE  = "grpc_server/single_request_client.py"

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def start_server(count: int) -> subprocess.Popen:
    """Launch the gRPC server with its own log file and return the Popen obj."""
    server_log = LOG_DIR / f"grpc-server-{count}-items.jsonl"

    cmd = [
        sys.executable,
        SERVER_FILE,
        "--host", HOST,
        "--port", PORT,
        "--pool-size", str(count),
        "--logger-name", f"grpc-server-{count}",
        "--log-file", str(server_log),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def run_client(count: int) -> int:
    """Run the client once and return the exit code."""
    client_log = LOG_DIR / f"grpc-client-{count}-items.jsonl"

    cmd = [
        sys.executable,
        CLIENT_FILE,
        "--host", HOST,
        "--port", PORT,
        "--count", str(count),
        "--logger-name", f"grpc-client-{count}",
        "--log-file", str(client_log),
    ]
    return subprocess.run(cmd).returncode


def stop_server(proc: subprocess.Popen) -> None:
    """Politely stop the server, killing it if it doesn’t exit in 5 s."""
    proc.send_signal(signal.SIGINT)
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=5)
    if proc.poll() is None:                          # still running ⟹ kill
        proc.kill()


# --------------------------------------------------------------------------- #
# Main loop                                                                   #
# --------------------------------------------------------------------------- #

def main() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    for size in SIZES:
        print(f"\n=== {size:_} items · {ITERATIONS} runs ===")

        # ------------------------------------------------------------------ #
        # 1. Start server                                                    #
        # ------------------------------------------------------------------ #
        print("🔧  Starting gRPC server …")
        server_proc = start_server(size)
        time.sleep(10)                                # give it a moment to bind

        try:
            # -------------------------------------------------------------- #
            # 2. Fire the client ITERATIONS times                            #
            # -------------------------------------------------------------- #
            for i in range(1, ITERATIONS + 1):
                print(f"  📥  Run {i:3d}/{ITERATIONS} … ", end="", flush=True)
                rc = run_client(size)
                if rc:
                    print(f"⚠️  client exit={rc}")
                    break
                print("✅")

        finally:
            # -------------------------------------------------------------- #
            # 3. Always tear the server down                                #
            # -------------------------------------------------------------- #
            print("🛑  Shutting down server …")
            stop_server(server_proc)

    print("\n🏁  All benchmarks finished.")
    print("\n🏁  Pausing to relieve pressure on memory")
    time.sleep(10)


if __name__ == "__main__":
    main()
