# bisq_light_client

a bisq client written in python intended to be fast.

## Getting Started

First, you need to generate the proto files in `proto` directory. refer to README file inside.

Minimum required python version is 3.10

## Run tests

```bash
# in root of project
python -m unittest discover -s tests -p '*_test.py'
```

## Credits

This project uses source codes taken from [Electrum](https://github.com/spesmilo/electrum) where applicable
