#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

INPUT_DATA_DIR = Path("data/single_request")
OUTPUT_DATA_DIR = Path("data/single_request")
ANCHOR_FILE_NAME = "time_anchor.jsonl"


def load_jsonl(path: Path) -> pd.DataFrame:
    return pd.read_json(path, lines=True)


def convert_jsonl_to_csv_latency(
    output_file_name: str = "single_request_latency.csv"
):
    output_csv = OUTPUT_DATA_DIR / output_file_name
    print(f"Generating CSV: {output_csv}…")

    # Prevent overwriting
    if output_csv.exists():
        raise FileExistsError(
            f"{output_csv} already exists. Remove it or choose a different name."
        )

    frames = []
    for protocol_dir in sorted(INPUT_DATA_DIR.iterdir()):
        if not protocol_dir.is_dir():
            continue

        print(f"Processing latency for protocol: {protocol_dir.name}")
        anchor_path = protocol_dir / ANCHOR_FILE_NAME
        if not anchor_path.exists():
            print(f"  ⚠️  No anchor file, skipping {protocol_dir.name}")
            continue

        anchors = load_jsonl(anchor_path)
        for anchor in anchors.itertuples(index=False):
            size       = int(anchor.size)
            perf_base  = anchor.perf_base_ns
            epoch_base = anchor.epoch_base_ns

            client_f = protocol_dir / f"client-{size}-items.jsonl"
            server_f = protocol_dir / f"server-{size}-items.jsonl"
            if not (client_f.exists() and server_f.exists()):
                print(f"  ⚠️  Missing client/server logs for size={size}, skipping")
                continue

            df_c = load_jsonl(client_f)  # t0, t_req, t_res, req_id
            df_s = load_jsonl(server_f)  # t_in, t_out, req_id

            df = df_c.merge(df_s, on="req_id", how="inner")
            df["mode"]           = protocol_dir.name
            df["size"]           = size
            df["perf_base_ns"]   = perf_base
            df["epoch_base_ns"]  = epoch_base

            frames.append(df)

    if not frames:
        print(f"No latency data found under {INPUT_DATA_DIR}. Exiting.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    cols = [
        "mode", "size", "req_id",
        "t0", "t_req", "t_res",
        "t_in", "t_out",
        "perf_base_ns", "epoch_base_ns",
        "req_size_bytes", "res_size_bytes",
    ]
    combined = combined[cols]

    # write it out
    combined.to_csv(output_csv, index=False)
    print(f"✅  Wrote {len(combined)} rows to {output_csv}")


def convert_jsonl_to_csv_usage(
    usage_side: str = "server",
    output_file_name: str = None
):
    """
    Merge all "usage-<side>-<size>-items.jsonl" under each protocol
    into one CSV.  `usage_side` must be either "server" or "client".

    - usage_side:       "server" or "client"
    - output_file_name: if None, defaults to "single_request_<side>_usage.csv"
    """
    # validate
    if usage_side not in ("server", "client"):
        raise ValueError("usage_side must be 'server' or 'client'")

    if output_file_name is None:
        output_file_name = f"single_request_{usage_side}_usage.csv"

    output_csv = OUTPUT_DATA_DIR / output_file_name
    print(f"Generating CSV: {output_csv}…")

    # Prevent overwriting
    if output_csv.exists():
        raise FileExistsError(
            f"{output_csv} already exists. Remove it or choose a different name."
        )

    frames = []
    for protocol_dir in sorted(INPUT_DATA_DIR.iterdir()):
        if not protocol_dir.is_dir():
            continue

        print(f"Processing {usage_side}-usage for protocol: {protocol_dir.name}")
        anchor_path = protocol_dir / ANCHOR_FILE_NAME
        if not anchor_path.exists():
            print(f"  ⚠️  No anchor file, skipping {protocol_dir.name}")
            continue

        anchors = load_jsonl(anchor_path)
        for anchor in anchors.itertuples(index=False):
            size       = int(anchor.size)
            perf_base  = anchor.perf_base_ns
            epoch_base = anchor.epoch_base_ns

            # pick the right usage file
            usage_f = protocol_dir / f"usage-{usage_side}-{size}-items.jsonl"
            if not usage_f.exists():
                print(f"  ⚠️  Missing {usage_side}-usage log for size={size}, skipping")
                continue

            df = load_jsonl(usage_f)  # ts, rss, cpu
            df["protocol"]       = protocol_dir.name
            df["size"]           = size
            df["usage_side"]     = usage_side
            df["perf_base_ns"]   = perf_base
            df["epoch_base_ns"]  = epoch_base

            frames.append(df)

    if not frames:
        print(f"No {usage_side}-usage data found under {INPUT_DATA_DIR!s}. Exiting.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    cols = [
        "protocol",
        "size",
        "usage_side",
        "ts",
        "rss",
        "cpu",
        "perf_base_ns",
        "epoch_base_ns",
    ]

    combined = combined[cols]

    combined.to_csv(output_csv, index=False)
    print(f"✅  Wrote {len(combined)} rows to {output_csv}")


if __name__ == "__main__":
    convert_jsonl_to_csv_latency()
    convert_jsonl_to_csv_usage(usage_side='server')
    convert_jsonl_to_csv_usage(usage_side='client')
