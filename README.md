
Generate protoBuf in server (optional)

```bash
python -m grpc_tools.protoc   -I ./proto   --python_out=./grpc_server   --grpc_python_out=./grpc_server   ./proto/records.proto
python -m grpc_tools.protoc   -I ./proto   --python_out=./rest_proto_server   --grpc_python_out=./rest_proto_server   ./proto/records.proto
```

Start gRPC server
```bash
python grpc_server/server.py --port 50051 --pool-size 1000 --logger-name grpc-server  --log-file data/test_grpc_server.jsonl
```

Start gRPC client
```bash
python grpc_server/single_request_client.py --host 127.0.0.1 --port 50051 --count 100 --logger-name grpc-client --log-file data/test_grpc_client.jsonl
```

gRPC single run test
```bash
python test_grpc_single_request.py 
```

Start rest + protobuf server
```bash
python rest_proto_server/server.py --port 8000 --pool-size 1000 --logger-name rest_proto_server  --log-file data/test_rest_proto_server.jsonl
```

Start rest + protobuf client
```bash
python rest_proto_server/single_request_client.py --host 127.0.0.1 --port 8000 --count 100 --logger-name rest_proto_server --log-file data/test_test_proto_client.jsonl
```

rest + protobuf single run test
```bash
python test_rest_proto_single_request.py 
```

Start rest + json server
```bash
python rest_json_server/server.py --port 8000 --pool-size 1000 --logger-name rest_json_server  --log-file data/test_rest_json_server.jsonl
```

Start rest + json client
```bash
python rest_json_server/single_request_client.py --host 127.0.0.1 --port 8000 --count 100 --logger-name rest_json_server --log-file data/test_rest_json_client.jsonl
```

rest + json single run test
```bash
python test_rest_json_single_request.py 
```

# Measurement
## Unified timestamp map
| Symbol      | Recorded **where**                                       | Code line(s) in each variant                                                                                                 | **Use these deltas** | What the delta represents                                                                                                                                    |
| ----------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `t0`        | first statement in every client                          | `t0 = perf_counter_ns()`                                                                                                     | `t_req − t0`         | **Client “setup” only:** create `req_id`, headers/URL, channel (gRPC) and build the *in-memory* request object (dict or protobuf). No (de)serialisation yet. |
| `t_req`     | immediately before the blocking I/O that ships bytes     | • REST-JSON / REST-Proto → just before `requests.post(...)` <br>• gRPC-Proto → just before `stub.getRecordListResponse(...)` | `t_res − t_req`      | **Client-observed round-trip latency** – body **serialisation**, network both directions, server work, **deserialisation** of the reply.                     |
| **`t_in`**  | first line in the server handler                         | FastAPI handler entry (REST) <br>gRPC servicer entry                                                                         | `t_in − t_req`       | **Uplink latency** – client→server network + server framework receive & parse. *Requires clock sync.*                                                        |
| **`t_out`** | callback after server has flushed response bytes         | `background_tasks.add_task(...)` (REST) <br>`context.add_done_callback(...)` (gRPC)                                          | `t_out − t_in`       | **Pure server time** – handler logic + response serialisation.                                                                                               |
| `t_res`     | first line after the blocking call returns on the client | right after `requests.post(...)` / `stub.…` returns                                                                          | `t_res − t_out`      | **Downlink latency** – server→client network + client framework parse/deserialise.                                                                           |
                                  |


## Composite metrics (apply to all three protocols)
| Metric                         | Formula         | Interpretation                                            |
| ------------------------------ | --------------- | --------------------------------------------------------- |
| **Client-observed round-trip** | `t_res − t_req` | What an end-user experiences.                             |
| **Pure server processing**     | `t_out − t_in`  | Business logic only, no network.                          |
| **Total in-app runtime**       | `t_res − t0`    | Whole client function, including setup.                   |
| **Uplink latency**             | `t_in − t_req`  | Network + server demux/parse (needs synchronised clocks). |
| **Downlink latency**           | `t_res − t_out` | Network + client demux/parse (needs synchronised clocks). |


- In REST + JSON, res.json() is called before t_res.
- In REST + Proto, ParseFromString is called before t_res.
- In gRPC, deserialisation is inherent to the stub call and therefore also finished before t_res.

Hence t_req → t_res now captures the exact same work for REST-JSON, REST-Protobuf, and gRPC-Protobuf, giving strictly comparable latency numbers.