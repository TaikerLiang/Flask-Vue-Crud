"""
.. module:: conftest
   :platform: Ubuntu 18.04, linux & Mac OS
   :synopsis: initiation of testing

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""

import pytest
import datetime
from src import app


@pytest.fixture(scope="session")
def app_client():
    return app.test_client()
