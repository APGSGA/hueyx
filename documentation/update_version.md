# Update version

This document is written for collaborators and describes how to update the package on PyPi.
This tutorial as basically aligned with [python packaging tutorial](https://packaging.python.org/tutorials/packaging-projects/).


### Accounts

- [Test PyPi](https://test.pypi.org/user/apgsga/)
- [PyPi](https://pypi.org/user/apgsga/)

### Projects
- [hueyx on test PyPi](https://test.pypi.org/project/hueyx/)
- [hueyx on PyPi](https://pypi.org/project/hueyx/)


### Update version

Be sure you have installed the `requirements.txt` and your pip is up to date.

- Update version in setup.py.
- Update [release_notes.md](../release_notes.md).
- Build library.
```bash
# Build library
python3 setup.py sdist bdist_wheel
```
- Upload the new packages to test PyPi
```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

- Test it with a project.
```bash
pip install -i https://test.pypi.org/simple/ hueyx
```

- If everything is ok, upload the packge to PyPi.
```bash
twine upload dist/*
```

