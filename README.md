# bisq_light_client

a bisq client written in python intended to be fast.

## Getting Started

Minimum required python version is 3.9

### 1. Install dependencies

```bash
# in project root:
python -m pip install -r requirements.txt
# or on debian:
sudo apt install python3-txtorcon python3-twisted python3-tqdm python3-grpcio python3-cryptography python3-pycryptodome python3-requests python3-socks python3-psutil libsecp256k1-dev python3-sortedcontainers python3-aiohttp python3-async-timeout python3-aiorpcx python3-certifi python3-dnspython python3-six python3-openssl python3-grpc-tools tor
```

It is a priority to make the project runnable without installing deps through pip. please let me know if something does not work.

### 2. Generate proto files

```bash
# generate the python files
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. --proto_path=proto grpc.proto pb.proto grpc_extra.proto
# Or this if you are using debian packages and command above does not work:
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --proto_path=proto grpc.proto pb.proto grpc_extra.proto
```

Note: files are expected to be generated at the root of project, beside `run_client.py`

### Note about deps

Since we use some parts of electrum and in part [libsecp256k1](https://github.com/bitcoin-core/secp256k1), you can follow the instructions for building or installing libsecp256k1 from [electrum's readme](https://github.com/spesmilo/electrum/blob/4.4.5/README.md)

windows users can check [here](https://github.com/spesmilo/electrum/blob/4.4.5/contrib/build-wine/README_windows.md#2-install-libsecp256k1)

compiled binary must be placed in `electrum_min` directory beside `ecc_fast.py` file.

## Run tests

```bash
# in root of project
python -m unittest discover -s tests -p '*_test.py'
```

## Run client

```bash
python run_client.py
```

## Credits

This project uses source codes taken from [Electrum](https://github.com/spesmilo/electrum) where applicable
