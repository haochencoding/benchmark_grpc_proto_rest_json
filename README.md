
Generate protoBuf in server (optional)

```bash
python -m grpc_tools.protoc   -I ./proto   --python_out=./grpc_server   --grpc_python_out=./grpc_server   ./proto/records.proto
python -m grpc_tools.protoc   -I ./proto   --python_out=./rest_proto_server   --grpc_python_out=./rest_proto_server   ./proto/records.proto
```

Start gRPC server
```bash
python grpc_server/server.py --port 50051 --pool-size 1000 --logger-name grpc-server  --log-file data/test-grpc-server.jsonl
```

Start gRPC client
```bash
python grpc_server/single_request_client.py --host 127.0.0.1 --port 50051 --count 100 --logger-name grpc-client --log-file data/test-grpc-client.jsonl
```

gRPC single run test
```bash
python test_grpc_single_request.py 
```

Start rest + protobuf server
```bash
python rest_proto_server/server.py --port 8000 --pool-size 1000 --logger-name rest_proto_server  --log-file data/test-rest-proto-server.jsonl
```

Start rest + protobuf client
```bash
python rest_proto_server/single_request_client.py --host 127.0.0.1 --port 8000 --count 100 --logger-name rest_proto_server --log-file data/test-rest-proto-client.jsonl
```

rest + protobuf single run test
```bash
python test_rest_proto_single_request.py 
```

Start rest + json server
```bash
python rest_json_server/server.py --port 8000 --pool-size 1000 --logger-name rest_json_server  --log-file data/test-rest-json-server.jsonl
```

Start rest + json client
```bash
python rest_proto_server/single_request_client.py --host 127.0.0.1 --port 8000 --count 100 --logger-name rest_proto_server --log-file data/test-rest-json-client.jsonl
```

rest + json single run test
```bash
python test_rest_proto_single_request.py 
```

# Measurement
## Unified timestamp map
| Symbol      | Recorded **where**                                                                         | Exact code line(s) in each variant                                                                                                              | **Use these deltas** | What the delta represents                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `t0`        | very first statement inside every client function                                          | *all 3*: `t0 = perf_counter_ns()`                                                                                                               | `t_req − t0`         | **Client-side set-up** – create `req_id`, headers, URLs, channel/stub (gRPC) **but not body-serialization**.                  |
| `t_req`     | immediately **before the blocking I/O call** that hands the request bytes to the runtime   | • **REST-JSON / REST-Proto** → right before `requests.post(…)`  <br>• **gRPC-Proto** → right before `stub.getRecordListResponse(…)`             | `t_res − t_req`      | **Client-observed end-to-end latency** – body-serialization + wire both ways + server work.                                   |
| **`t_in`**  | first line executed in the server handler                                                  | • **REST-JSON / REST-Proto** → first line of `@app.post("/records")` in FastAPI  <br>• **gRPC-Proto** → first line of `getRecordListResponse()` | `t_in − t_req`       | **Uplink network latency** (client ➜ server) + server framework parse/deserialise overhead.<br>*Needs clock synchronisation.* |
| **`t_out`** | callback executed **after** the server has serialised the reply and flushed status/headers | • `context.add_done_callback(…)` in gRPC server  <br>• `background_tasks.add_task(log_rpc, …)` in FastAPI servers                               | `t_out − t_in`       | **Pure server time** – your handler logic + response serialisation.                                                           |
| `t_res`     | first line after the blocking I/O returns on the client                                    | *all 3*: right after `requests.post` / `stub.…` returns                                                                                         | `t_res − t_out`      | **Downlink network latency** (server ➜ client) + client framework parse/deserialise time.                                     |


## Composite metrics (apply to all three protocols)
| Metric name                    | Formula         | Interpretation                               |
| ------------------------------ | --------------- | -------------------------------------------- |
| **Client-observed round-trip** | `t_res − t_req` | What an end-user “feels”.                    |
| **Pure server processing**     | `t_out − t_in`  | Business logic only – no network.            |
| **(End-to-End?) Total in-app runtime**       | `t_res − t0`    | Entire client call, including set-up.        |
| **Uplink latency**             | `t_in − t_req`  | Network + server demux; needs synced clocks. |
| **Downlink latency**           | `t_res − t_out` | Network + client demux; needs synced clocks. |
