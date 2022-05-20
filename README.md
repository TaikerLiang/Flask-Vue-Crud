
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
pip install -r requirements-dev.txt
```

### Run Spider by command

```
cd src/crawler/spiders/
scrapy runspider carrier_eglv_multi.py -a mbl_nos=141101170827 -a task_ids=120509
```

## Run Tests

```
pytest -x test
```

## Deploy to Scrapy Cloud

Currently, shub 2.14.1 require click 7.0 but some of our packages are using click 8.0 or later.
We suggest use [shub binary](https://github.com/scrapinghub/shub/releases/tag/v2.14.1) as a workaround.
Once [this issue](https://github.com/scrapinghub/shub/pull/416) is resolved, we can use pip version again.

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


## Local Solution

```
$ cd local
# to check the detail arguments
$ python local_crawler.py --help
# for prd
python local_crawler.py -m prd
# for prd with proxy
python local_crawler.py -m prd --proxy
# for dev
python local_crawler.py -m dev -t carrier -n 2
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

## Commit template

Add commit message template:

```bash
git config commit.template .git-commit-template
```

## Q&A

* Error: “chromedriver” cannot be opened because the developer cannot be verified. Unable to launch the chrome browser on Mac os

```
$ xattr -d com.apple.quarantine chromedriver
```
