
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
## Timestamps
| Symbol      | Recorded **where**                                       | Code line(s) in each variant                                                                                                 |
| ----------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `t0`        | first statement in every client                          | `t0 = perf_counter_ns()`                                                                                                     |
| `t_req`     | immediately before the blocking I/O that ships bytes     | • REST-JSON / REST-Proto → just before `requests.post(...)` <br>• gRPC-Proto → just before `stub.getRecordListResponse(...)` |
| **`t_in`**  | first line in the server handler                         | FastAPI handler entry (REST) <br>gRPC servicer entry                                                                         |                                      |
| **`t_out`** | callback after server has flushed response bytes         | `background_tasks.add_task(...)` (REST) <br>`context.add_done_callback(...)` (gRPC)                                          |
| **`t_res`** | first line after the blocking call returns on the client | right after `requests.post(...)` / `stub.…` returns                                                                          |

**Note on why t_res is measured after client parsing/deserialisation:**
- In gRPC, deserialisation is inherent to the stub call and therefore also finished before t_res. It is difficult to mark the time before deserialisation in python. So the changes are made in other protocols to make the measurement consistent.
- In REST + JSON, res.json() is called before t_res.
- In REST + Proto, ParseFromString is called before t_res.


## Duration

## Duration Components (Phases)
| Variable               | Metric                         | Formula           | Interpretation                                                                                     |
| ---------------------- | ------------------------------ | ----------------- | -------------------------------------------------------------------------------------------------- |
| `client_setup_ns`      | **Client setup time**         | `t_req − t0`      | Preparation only: create `req_id`, headers/URL, channel  (gRPC), and build the in-memory request object (dict or protobuf). No (de)serialisation or network yet. |
| `uplink_latency_ns`    | **Uplink latency**             | `t_in − t_req`    | Client→server network + server receive & parse. Requires clock sync, if not on same machine.|
| `outbound_latency_ns`    | **Outbound latency**             | `t_0 − t_req`    | All client-side prep + network→server. Because in gRPC, the channel is build during client setup, while REST build the conneciton during uplink latency phase. It is unfair to seperate them in comparison.|
| `server_processing_ns` | **Pure server processing**     | `t_out − t_in`    | Pure server processing time: handler logic + response serialisation, no network. |
| `downlink_latency_ns`  | **Downlink latency**           | `t_res − t_out`   | server→client network + client framework receive, parse/deserialise. |

### Total Durations (End-to-End) Metric
| Variable               | Metric                         | Formula           | Interpretation                                                                                     |
| ---------------------- | ------------------------------ | ----------------- | -------------------------------------------------------------------------------------------------- |
| `round_trip_ns`        | **Client-observed round-trip** | `t_res − t_req`   | What an end-user experiences: body **serialisation**, network both directions, server work, **deserialisation** of the reply.                                                                     |
| `total_runtime_ns`     | **Total in-app runtime**       | `t_res − t0`      | Whole client function, including setup.                                                            |
