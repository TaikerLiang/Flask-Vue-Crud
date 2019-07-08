# flask-vue-crud-server

## Setting

```
$ pip3 install -r requirements.txt
```

## Folder Explanation

* docs: api documents
* src: source code
* tests: unit test & integration test
* scripts: for aws codedeploy
* migration: db migration

## Document

```
$ apidoc -i src -o docs
```

## Testing

```
$ export FLASK_APP=./run.py
$ flask test
```

## migration

```
$ flask db upgrade
```


