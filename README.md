

## Environment for Develop

Install requirements

```bash
pip install -U pip setuptools
pip install -e '.[dev]'
```


## Run Tests

```bash
epsc test
```


## Generate Package Requirements

Install `pip-tools`

```bash
pip install -U pip-tools
```

Compile

```bash
pip-compile -U --output-file src/requirements-scrapy_cloud.txt src/requirements-scrapy_cloud.in
pip-compile -U --output-file src/requirements-app.txt src/requirements-app.in
pip-compile -U --output-file requirements-dev.txt requirements-dev.in
```

Verify

```
pip install -e '.[dev]'
```
