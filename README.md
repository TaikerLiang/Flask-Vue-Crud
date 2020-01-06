

## Environment for Develop

### System Requirements

Install Chrome Browser

Install PhantomJS (Mac)

```bash
brew tap homebrew/cask
brew cask install phantomjs
```

### Install Python Packages

```bash
pip install -U pip setuptools
pip install -e '.[dev]'
```


## Run Tests

```bash
epsc test
```


## Deploy to Scrapy Cloud

### (Prepare) Docker Login

* Username is your API key
* Password is '` `' (one empty space)

```bash
docker login images.scrapinghub.com
```

### (Prepare) scrapinghub.yml

Sample

```yaml
projects:
  default:
    id: ######

image: true
```

### Deploy Image 

```bash
shub image upload

# ----- equivalent to -----
# shub image build
# shub image push
# shub image deploy
```


## Generate Package Requirements

Install `pip-tools`

```bash
pip install -U pip-tools
```

Compile

```bash
pip-compile -U --output-file src/requirements-app.txt src/requirements-app.in
pip-compile -U --output-file requirements-dev.txt requirements-dev.in
```

Verify

```
pip install -e '.[dev]'
```
