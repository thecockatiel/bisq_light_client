# bisq_light_client

a bisq client written in python intended to be fast.

## Getting Started

First, you need to generate the proto files in `proto` directory. refer to README file inside.

Minimum required python version is 3.10

## Installing deps

```bash
# in project root:
python -m pip install -r requirements.txt
# or on debian:
sudo apt install python3-txtorcon python3-twisted python3-tqdm python3-grpcio python3-cryptography python3-pycryptodome python3-requests python3-socks python3-psutil libsecp256k1-dev python3-sortedcontainers python3-aiohttp python3-async-timeout
```

It is a priority to make the project runnable without installing deps through pip. please let me know if something does not work.

## Note about deps

Since we use some parts of electrum and in part [libsecp256k1](https://github.com/bitcoin-core/secp256k1), you can follow the instructions for building or installing libsecp256k1 from [electrum's readme](https://github.com/spesmilo/electrum/blob/4.4.5/README.md)

windows users can check [here](https://github.com/spesmilo/electrum/blob/4.4.5/contrib/build-wine/README_windows.md#2-install-libsecp256k1)

compiled binary must be placed in `electrum_min` directory beside `ecc_fast.py` file.

## Run tests

```bash
# in root of project
python -m unittest discover -s tests -p '*_test.py'
```

## Credits

This project uses source codes taken from [Electrum](https://github.com/spesmilo/electrum) where applicable
