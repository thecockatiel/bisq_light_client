# Experiments

For development purposes only, ignore this.

## Run tor

linux:

```bash
# from experiments directory:
PYTHONPATH=$(dirname $PWD) python run_tor.py
# from root directory:
PYTHONPATH=$PWD python experiments/run_tor.py
```

windows powershell:

```powershell
# from experiments directory
$env:PYTHONPATH = (get-item (Get-Location)).parent.FullName; python run_tor.py
# from root directory:
$env:PYTHONPATH = (Get-Location).Path; python experiments/run_tor.py
```
