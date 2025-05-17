import time
import json
from pathlib import Path


def write_timeline_anchor(file_path: str, mode: str, size: int) -> None:
    """
    Write out a JSON‐line “timeline anchor” tying perf_counter_ns()
    to epoch time.

    Args:
        file_path: where to write the .jsonl anchor
        mode:     e.g. "grpc" or "rest_proto"
        size:      the current workload size
    """
    perf_base_ns = time.perf_counter_ns()
    epoch_base_ns = time.time_ns()
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as fh:
        json.dump({
            "mode":          mode,
            "size":          size,
            "perf_base_ns":  perf_base_ns,
            "epoch_base_ns": epoch_base_ns,
        }, fh)
        fh.write("\n")
