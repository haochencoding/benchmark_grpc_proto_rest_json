#!/usr/bin/env python3
"""
Simple one-shot client for the FastAPI JSON service.
"""

import argparse
import json
import secrets
import sys
from pathlib import Path
from time import perf_counter_ns

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, log_client            # noqa: E402

# --------------------------------------------------------------------------- #
def fetch_records(host: str, port: int, count: int, logger) -> None:
    req_id = f"{secrets.randbits(64):016x}"

    # Overall lifecycle start
    t0 = perf_counter_ns()

    # 1. build pure-Python request object (dict) ────────────────────────────
    request_obj = {"count": count}

    headers = {
        "content-type": "application/json",
        "accept":       "application/json",
        "req-id":       req_id,
    }

    url = f"http://{host}:{port}/records"

    # 2. start latency window – serialisation happens *inside* requests ----
    t_req = perf_counter_ns()

    # Request serialisation, posting, and receiving response
    res = requests.post(url, json=request_obj, headers=headers)
    
    if res.status_code != 200:
        print(f"Server error: {res.status_code} {res.text}")
        return

    # Decode from bytes to a python object
    res.json()   # decode just to assert correctness

    # 3. Measure response time
    # I.e., the time the received object is usable as an object with the client
    t_res = perf_counter_ns()

    log_client(logger, t0=t0, t_req=t_req, t_res=t_res, req_id=req_id)
    print("Finished")

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch records from REST-JSON server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--logger-name", required=True)
    ap.add_argument("--log-file", type=Path, required=True)
    args = ap.parse_args()

    logger = setup_logger(args.logger_name, args.log_file)
    fetch_records(args.host, args.port, args.count, logger)
