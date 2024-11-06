# Bisq proto files

These files are downloaded from <https://github.com/bisq-network/bisq/blob/master/proto/src/main/proto>
make sure to update these when necessary

## Generate files

```bash
# install the required tools:
python -m pip install -r ../requirements.txt
# generate the python files
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. grpc.proto pb.proto
```
