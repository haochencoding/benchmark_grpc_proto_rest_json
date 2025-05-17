#!/usr/bin/env python3
"""
Simple one-shot client for the FastAPI protobuf service.
"""

import argparse
import secrets
import sys
from pathlib import Path
from time import perf_counter_ns

import requests

import records_pb2 as pb2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, log_client        # noqa: E402


# --------------------------------------------------------------------------- #
# Main client logic                                                           #
# --------------------------------------------------------------------------- #

def fetch_records(host: str, port: int, count: int, logger) -> None:
    req_id = f"{secrets.randbits(64):016x}"

    # Overall lifecycle start
    t0 = perf_counter_ns()

    # 1. build request-obj (protobuf message) ------------------------------
    req_pb = pb2.RecordListRequest(count=count)
    headers = {
        "content-type": "application/x-protobuf",
        "accept":       "application/x-protobuf",
        "req-id":       req_id,
    }

    url = f"http://{host}:{port}/records"

    # 2. latency window – serialise right in the call ----------------------
    t_req = perf_counter_ns()

    # Request serialisation, posting, and receiving response
    res = requests.post(url, data=req_pb.SerializeToString(), headers=headers)

    if res.status_code != 200:
        print(f"Server error: {res.status_code} {res.text}")
        return

    # Decode response (bytes) to a python object
    resp_pb = pb2.RecordListResponse.FromString(res.content)

    # Uncomment the line below to see the print record
    # print(resp_pb.records[0])

    # 3. Measure response time
    # I.e., the time the received object is usable as an object with the client
    t_res = perf_counter_ns()

    # 4. Measure body size after query finish
    req_size_bytes = len(req_pb.SerializeToString())
    resp_size_bytes = len(res.content)

    log_client(
        logger,
        t0=t0,
        t_req=t_req,
        t_res=t_res,
        req_id=req_id,
        req_size_bytes=req_size_bytes,
        resp_size_bytes=resp_size_bytes
    )

    print("Finished")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fetch records from a Timestream gRPC server")
    ap.add_argument("--host", default="127.0.0.1", help="Server hostname or IP (default: %(default)s)")
    ap.add_argument("--port", type=int, default=50051, help="Server port (default: %(default)s)")
    ap.add_argument("--count", type=int, default=100, help="Number of records to request (default: %(default)s)")
    ap.add_argument(
        "--logger-name", required=True,
        help="Name to give the logger instance (must match server if you want unified logs)",
    )
    ap.add_argument(
        "--log-file", type=Path, required=True,
        help="Path for the JSON-lines log file",
    )
    args = ap.parse_args()

    logger = setup_logger(args.logger_name, args.log_file)
    fetch_records(args.host, args.port, args.count, logger)
