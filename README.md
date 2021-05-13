## Environment for Develop

### System Requirements

Install Chrome Browser(mac)

```bash
brew tap homebrew/cask
brew cask install google-chrome

# version check
# install through package manager
google-chrome --version

# or
open -a "Google Chrome"
# type chrome://version/ on url
```

Install Chrome Driver(Mac)

```bash
brew tap homebrew/cask
brew cask install chromedriver

# check
chromedriver --version  # need to be same as browser
```

Install PhantomJS (Mac)

```bash
brew tap homebrew/cask
brew cask install phantomjs
```

### Prepare Python Env

Python version: `3.8.2`

```bash
pyenv install [PYTHON_VERSION]
pyenv virtualenv [PYTHON_VERSION] [PYTHON-VENV-NAME]
```

```bash
cd [PROJECT-ROOT]
pyenv local [PYTHON-VENV-NAME]
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
shub image upload [PROJECT-ID]

# ----- equivalent to -----
# shub image build [PROJECT-ID]
# shub image push [PROJECT-ID]
# shub image deploy [PROJECT-ID]
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


## Pre-commit

```
$ pre-commit install
```
