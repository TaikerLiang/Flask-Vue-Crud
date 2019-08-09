"""
.. module:: run
   :platform: Ubuntu 18.04 & Mac OS
   :synopsis: Main function of flask service

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""

from flask import Flask, jsonify, request
from src import app
import os
import logging


@app.cli.command()
def test():
    os.system("pytest -x")


# sanity check route
@app.route("/ping", methods=["GET"])
def ping_pong():
    return jsonify("pong!")


if __name__ == "__main__":
    app.run(use_reloader=False)

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)