"""
.. module:: run
   :platform: Ubuntu 18.04 & Mac OS
   :synopsis: Main function of flask service

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""

from flask import Flask, jsonify, request
from src import app, db
import os
import logging


@app.cli.command()
def test():
    
    with app.app_context():
        db.reflect()
        db.drop_all()
        db.create_all()
    
    os.system("pytest -x")

@app.cli.command()
def initdb():
    """Initialize the database."""
    print("Init the db")
    db.create_all()

# sanity check route
@app.route("/ping", methods=["GET"])
def ping_pong():
    return jsonify("pong!")


@app.route("/", methods=["GET"])
def hello():
    return jsonify({"err": 0, "env": os.getenv("ENV"), "err_msg": "Welcome to Flask asg {}!!".format(app.config["BRANCH"])})


if __name__ == "__main__":
    app.run(use_reloader=False)

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)