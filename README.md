# bisq_light_client

a bisq client written in python intended to be fast.

## Getting Started

Minimum required python version is 3.9

### 1. Clone and init submodules

```bash
# fresh clone:
git clone --recurse-submodules --shallow-submodules https://github.com/thecockatiel/bisq_light_client.git

# if you have already cloned the repo without `--recurse-submodules`:
cd bisq_light_client && git submodule update --init --recursive --depth=1
```

### 2. Install dependencies

```bash
# in project root:
python3 -m pip install -r requirements.txt
# or on debian:
sudo apt-get install python3-txtorcon python3-twisted python3-tqdm python3-grpcio python3-cryptography python3-pycryptodome python3-requests python3-socks python3-psutil libsecp256k1-dev python3-sortedcontainers python3-aiohttp python3-async-timeout python3-aiorpcx python3-certifi python3-dnspython python3-six python3-openssl python3-grpc-tools tor python3-attr python3-jsonpatch
# depending on your distro and package availability:
sudo apt-get install python3-pyqt6
# or
sudo apt-get install python3-pyqt5
```

It is a priority to make the project runnable without installing deps through pip. please let me know if something does not work.

### 3. Generate proto files

```bash
# generate the python files
python3 -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. --proto_path=proto pb.proto grpc.proto grpc_extra.proto
# Or this if you are using debian packages and command above does not work:
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. --proto_path=proto pb.proto grpc.proto grpc_extra.proto
```

Note: files are expected to be generated at the root of project, beside `run_client.py`

### Note about deps

Since we use some parts of electrum and in part [libsecp256k1](https://github.com/bitcoin-core/secp256k1), you can follow the instructions for building or installing libsecp256k1 from [electrum's readme](https://github.com/spesmilo/electrum/blob/4.4.5/README.md)

windows users can check [here](https://github.com/spesmilo/electrum/blob/4.4.5/contrib/build-wine/README_windows.md#2-install-libsecp256k1)

compiled binary must be placed in `electrum_min` directory beside `ecc_fast.py` file.

## Run tests

```bash
# in root of project
python3 -m unittest discover -s tests -p '*_test.py'
```

## Run daemon

```bash
python3 run_daemon.py
```

## Credits

This project uses source codes taken from [Electrum](https://github.com/spesmilo/electrum) where applicable
