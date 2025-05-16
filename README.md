
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
python rest_proto_server/server.py --port 50051 --pool-size 1000 --logger-name rest_proto_server  --log-file data/test-rest-proto-server.jsonl
```

Start rest + protobuf client
```bash
python rest_proto_server/single_request_client.py --host 127.0.0.1 --port 50051 --count 100 --logger-name rest_proto_server --log-file data/test-rest-proto-client.jsonl
```

rest + protobuf single run test
```bash
python test_rest_proto_single_request.py 
```
# Measurement
| Symbol      | Taken at…                                                                                | **Use these deltas** | Meaning                                                                                                          |
| ----------- | ---------------------------------------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `t0`        | very first line in the client script                                                     | `t_req − t0`         | **Client-side preparation** (create channel/stub and build the protobuf request).                                |
| `t_req`     | exactly before the blocking `stub.getRecordListResponse()` call                          | `t_res − t_req`      | **Full RPC latency as seen by the client** (wire time both directions **plus** server work).                     |
| **`t_in`**  | first line inside the service method on the server                                       | `t_in − t_req`       | **Request-wire latency** (network + server HTTP/2 parsing + deserialization).<br>*Requires synchronised clocks.* |
| **`t_out`** | callback fired **after** the server has serialised the reply and written status/trailers | `t_out − t_in`       | **Pure server processing time** (your handler + response marshalling).                                           |
| `t_res`     | first line after the call returns on the client                                          | `t_res − t_out`      | **Response-wire latency** (server→client network + client deserialization).                                      |

Common composite metrics
| Metric                         | Formula         | Comment                                  |
| ------------------------------ | --------------- | ---------------------------------------- |
| **Pure server time**           | `t_out − t_in`  | excludes all network overhead.           |
| **Client-observed round-trip** | `t_res − t_req` | what end-users feel.                     |
| **End-to-end in-app runtime**  | `t_res − t0`    | entire client function, including setup. |
| **Network (uplink)**           | `t_in − t_req`  | only valid if clocks are synced.         |
| **Network (downlink)**         | `t_res − t_out` | idem.                                    |
