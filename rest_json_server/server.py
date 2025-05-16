#!/usr/bin/env python3
"""
FastAPI server that speaks **JSON** over HTTP.

Request  body: {"count": <int>}
Response body: {"records": [<Record>, …]}

The logger & CLI flags match the protobuf server so post-processing tools
stay unchanged.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from time import perf_counter_ns

from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, log_rpc                # noqa: E402
from utils.constants import PROTOTYPE_RECORD                  # identical prototype

# --------------------------------------------------------------------------- #
# App factory                                                                 #
# --------------------------------------------------------------------------- #
def create_app(pool_size: int, logger: logging.Logger) -> FastAPI:
    records = [PROTOTYPE_RECORD.copy() for _ in range(pool_size)]

    app = FastAPI(title="Timestream REST (JSON)")

    @app.post("/records", response_class=Response)
    async def get_record_list(request: Request,
                              background_tasks: BackgroundTasks) -> Response:
        t_in = perf_counter_ns()

        # ---------- parse / validate JSON body ---------------------------- #
        try:
            payload = await request.json()
            count = int(payload["count"])
        except (ValueError, KeyError, json.JSONDecodeError):
            raise HTTPException(400, "Body must be JSON: {\"count\": <int>}")

        if count > pool_size:
            raise HTTPException(400, "Requested count exceeds pool size")

        # ---------- build JSON response ----------------------------------- #
        body = json.dumps({"records": records[:count]})

        # ---------- deferred logging -------------------------------------- #
        req_id = request.headers.get("req-id")
        background_tasks.add_task(log_rpc, logger, t_in=t_in, req_id=req_id)

        return Response(content=body, media_type="application/json")

    return app

# --------------------------------------------------------------------------- #
# Runner                                                                      #
# --------------------------------------------------------------------------- #
def serve(host: str, port: int, pool_size: int,
          logger_name: str, log_file_path: Path) -> None:
    logger = setup_logger(logger_name, log_file_path)
    app = create_app(pool_size, logger)

    print(f"REST-JSON server running on http://{host}:{port}")
    uvicorn.run(app,
                host=host,
                port=port,
                log_level="error")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Launch the REST-JSON server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True, help="Port to listen on")
    ap.add_argument("--pool-size", type=int, required=True, help="Number of records to pre-allocate")
    ap.add_argument("--logger-name", required=True)
    ap.add_argument("--log-file", type=Path, required=True)
    args = ap.parse_args()

    try:
        serve(args.host, args.port, args.pool_size,
              args.logger_name, args.log_file)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down REST-JSON server")
