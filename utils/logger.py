import logging
import sys
import json
from time import perf_counter_ns 


def setup_logger(name: str, log_file_path: str) -> logging.Logger:
    """
    Configure and return a logger that writes JSON lines to stdout and a file.

    Parameters
    ----------
    name : str
        Logger name.
    log_file_path : str
        Path to the log file.
    """
    # Configure root logger to write to stdout and file
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_file_path)
        ]
    )

    # Create and return named logger
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    return log


def log_rpc(
        log: logging.Logger,
        *,
        t_in: float,
        req_id: str
        ) -> None:
    t_out = perf_counter_ns()
    log.info(
        json.dumps(
            {"t_in": t_in, "t_out": t_out, "req_id": req_id},
            separators=(",", ":"),
        )
    )


def log_client(
        log: logging.Logger,
        *,
        t0: float,
        t_req: float,
        t_res: float,
        req_id: str,
        req_size_bytes=int,
        res_size_bytes=int
        ) -> None:
    log.info(
        json.dumps(
            {
                "t0": t0,
                "t_req": t_req,
                "t_res": t_res,
                "req_id": req_id,
                "req_size_bytes": req_size_bytes,
                "res_size_bytes": res_size_bytes
                },
            separators=(",", ":"),
        )
    )
