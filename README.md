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
```

gui dependencies:

```bash
sudo apt-get install python3-qrcode python3-pyqt5 qtbase5-dev qttools5-dev-tools pyqt5-dev-tools python3-matplotlib-qt5
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

## Simplex address

You can contact me on Simplex: [Link](https://simplex.chat/contact#/?v=2-7&smp=smp%3A%2F%2FPtsqghzQKU83kYTlQ1VKg996dW4Cw4x_bvpKmiv8uns%3D%40smp18.simplex.im%2FGfB7KGndhLe8PxTPjtIIm8BV0vv6wGKA%23%2F%3Fv%3D1-4%26dh%3DMCowBQYDK2VuAyEAj_mmVKhbUHj5RMgQrydsXH75xo3v1qb-dG2IhaA1Ik0%253D%26q%3Dc%26srv%3Dlyqpnwbs2zqfr45jqkncwpywpbtq7jrhxnib5qddtr6npjyezuwd3nqd.onion)
