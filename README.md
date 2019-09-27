

## Environment for Develop

Install requirements

```bash
pip install -U pip setuptools
pip install -r requirements-dev.txt
```


## Run Tests

```bash
docker-compose -f docker-compose.test.yml up --build --force-recreate
docker-compose -f docker-compose.test.yml down --remove-orphans
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
pip-compile -U --output-file requirements-test.txt requirements-test.in
pip-compile -U --output-file requirements-deploy.txt requirements-deploy.in
pip-compile -U --output-file requirements-dev.txt requirements-dev.in
```
