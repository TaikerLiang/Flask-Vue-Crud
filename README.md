# Developing a Single Page App with Flask and Vue.js

### Want to learn how to build this?

Check out the [post](https://testdriven.io/developing-a-single-page-app-with-flask-and-vuejs).

## Want to use this project?

1. Fork/Clone

1. Run the server-side Flask app in one terminal window:

    ```sh
    $ cd server
    $ python3.7 -m venv env
    $ source env/bin/activate
    (env)$ pip install -r requirements.txt
    (env)$ python app.py
    ```

    Navigate to [http://localhost:5000](http://localhost:5000)

1. Run the client-side Vue app in a different terminal window:

    ```sh
    $ cd client
    $ npm install
    $ npm run serve
    ```

    Navigate to [http://localhost:8080](http://localhost:8080)

## Start Container

```
$ docker-compose up --build
```

After starting, navigate to http://localhost:3000. Enjoy it.

P.S. If you have error `sh: vue-cli-service: not found`, just reinstall it and run docker-comopse again.

```
$ npm install -g @vue/cli
```

