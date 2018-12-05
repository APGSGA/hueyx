# hueyx

A django extension to run huey with multiple queues. It only supports Redis as storage.

### Usage

Install it with
```bash
pip install hueyx
```

### Update version

Be sure you have installed the `requirements.txt` and your pip is up to date.

1. Update version in setup.py.
2. Build library.

```bash
# Build library
python3 setup.py sdist bdist_wheel
```