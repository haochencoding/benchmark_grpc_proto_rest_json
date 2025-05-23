# ── MUST come first ──────────────────────────────────────
import os
import logging
os.environ.setdefault("GRPC_VERBOSITY", "none")   # or "none"
os.environ.pop("GRPC_TRACE", None)                 # disable tracing
logging.getLogger("grpc").setLevel(logging.ERROR)  # hide Python-level INFO

import grpc
import records_pb2 as pb2
import records_pb2_grpc as pb2_grpc
import asyncio

import argparse
from time import perf_counter_ns
import logging
from concurrent import futures
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent 
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, log_rpc
from utils.constants import PROTOTYPE_RECORD


class GrpcServer(pb2_grpc.TimestreamServicer):
    def __init__(self, pool_size: int, logger: logging.Logger):
        self.records = [PROTOTYPE_RECORD.copy() for _ in range(pool_size)]
        self._logger = logger
        self._pool_size = pool_size

    async def getRecordListResponse(
        self,
        request: pb2.RecordListRequest,
        context: grpc.aio.ServicerContext
    ) -> pb2.RecordListResponse:
        t_in = perf_counter_ns()

        if request.count > self._pool_size:
            # In the aio API you abort through the context:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                                "count exceeds pool size")

        # Metadata keys are bytes → decode to str, put into dict
        md = {k: v for k, v in context.invocation_metadata()}
        req_id = md.get("req-id")

        context.add_done_callback(lambda _: log_rpc(self._logger, t_in=t_in, req_id=req_id))

        return pb2.RecordListResponse(records=self.records[:request.count])


async def serve(host: str, port: int, pool_size: int, logger_name: str, log_file_path: Path):
    logger = setup_logger(logger_name, log_file_path)

    # gRPC message size limits
    max_msg = 160 * 1024 * 1024

    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", max_msg),
            ("grpc.max_receive_message_length", max_msg),
        ],
    )

    pb2_grpc.add_TimestreamServicer_to_server(
        GrpcServer(pool_size, logger), server
    )

    port = server.add_insecure_port(f"{host}:{port}")
    await server.start()
    print(f"gRPC server on {host}:{port}")
    await server.wait_for_termination()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Launch the gRPC Timestream server")
    ap.add_argument("--host", default="127.0.0.1", help="Bind address (default: %(default)s)")
    ap.add_argument("--port", type=int, help="Port to listen on")
    ap.add_argument("--pool-size", type=int, help="Number of prototype records to pre-allocate")
    ap.add_argument(
        "--logger-name",
        help="Name to give the logger instance",
    )
    ap.add_argument(
        "--log-file",
        type=Path,
        help="Path for the JSON-lines log file",
    )

    args = ap.parse_args()

    try:
        asyncio.run(serve(
            host=args.host,
            port=args.port,
            pool_size=args.pool_size,
            logger_name=args.logger_name,
            log_file_path=args.log_file
            ))
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down gRPC server")