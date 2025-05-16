"""
Simple client for the Timestream gRPC service.
Requests a list of records (default: 100) and prints them.

Usage:
  python fetch_records.py --host 127.0.0.1 --port 50051 --count 100
"""

import os
import logging
os.environ.setdefault("GRPC_VERBOSITY", "none")   # or "none"
os.environ.pop("GRPC_TRACE", None)                 # disable tracing
logging.getLogger("grpc").setLevel(logging.ERROR)  # hide Python-level INFO

import argparse
import grpc

import records_pb2 as pb2
import records_pb2_grpc as pb2_grpc

from time import perf_counter_ns
import sys
from pathlib import Path
import secrets

PROJECT_ROOT = Path(__file__).resolve().parent.parent 
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, log_client


def fetch_records(host: str, port: int, count: int, logger) -> None:
    req_id = f"{secrets.randbits(64):016x}"
    # 1. Timestamp of total-run lifecycle 
    t0 = perf_counter_ns()

    # Build chanenel and stub
    opts = [
        ("grpc.max_send_message_length", -1),
        ("grpc.max_receive_message_length", -1)
    ]
    channel = grpc.insecure_channel(f"{host}:{port}", options=opts)
    stub = pb2_grpc.TimestreamStub(channel)

    # Build protobuf request object
    request = pb2.RecordListRequest(count=count)

    # gRPC metadata must be a tuple of 2-tuples (key, value)
    meta = (("req-id", req_id),) 

    # Timestamp of send the request
    # RPC latency = t_res − t_req
    t_req = perf_counter_ns()
    response = stub.getRecordListResponse(request, metadata=meta)
    
    # Time of receiving the response
    t_res = perf_counter_ns()

    log_client(logger, t0=t0, t_req=t_req, t_res=t_res, req_id=req_id)
    print('Finished')


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