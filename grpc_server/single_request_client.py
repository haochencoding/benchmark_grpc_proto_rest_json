"""
Simple client for the Timestream gRPC service.
Requests a list of records (default: 100) and prints them.
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

    # 1. set-up channel & stub, build request-obj --------------------------
    opts = [
        ("grpc.max_send_message_length", -1),
        ("grpc.max_receive_message_length", -1)
    ]
    channel = grpc.insecure_channel(f"{host}:{port}", options=opts)
    stub = pb2_grpc.TimestreamStub(channel)

    # Build protobuf request object
    request_pb = pb2.RecordListRequest(count=count)
    meta = (("req-id", req_id),) 

    # 2. latency window – gRPC handles serialisation inside the call -------
    # Timestamp of send the request
    t_req = perf_counter_ns()

    # serialisation, posting, receiving response, and decoding response into an object
    response = stub.getRecordListResponse(request_pb, metadata=meta)
    
    # Uncomment the line below to print the first record
    # print(_response.records[0])

    # 3. Measure response time
    # I.e., the time the received object is usable as an object with the client
    t_res = perf_counter_ns()

    # 4. Measure body size after query finish
    req_size_bytes = len(request_pb.SerializeToString())
    res_size_bytes = len(response.SerializeToString())

    # 5. logging -----------------------------------------------------------
    log_client(
        logger,
        t0=t0,
        t_req=t_req,
        t_res=t_res,
        req_id=req_id,
        req_size_bytes=req_size_bytes,
        res_size_bytes=res_size_bytes
        )
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