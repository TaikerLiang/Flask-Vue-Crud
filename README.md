

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
pip-compile -U --output-file requirements-base.txt requirements-base.in
pip-compile -U --output-file requirements-tests.txt requirements-tests.in
pip-compile -U --output-file requirements-deploy.txt requirements-deploy.in
pip-compile -U --output-file requirements-dev.txt requirements-dev.in
```

Verify

```
pip install -e '.[dev,tests,deploy]'
```
