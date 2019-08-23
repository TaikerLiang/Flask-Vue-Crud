"""
.. module:: conftest
   :platform: Ubuntu 18.04, linux & Mac OS
   :synopsis: initiation of testing

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""

from src import app, db
from src.models.books import Book
import uuid
import pytest
import datetime

@pytest.fixture(scope="session")
def app_client():
    return app.test_client()


@pytest.fixture(scope="session")
def books():
    _book = Book(uuid.uuid4().hex, "On the Road", "Jack Kerouac", 1)
    db.session.add(_book)
    _book = Book(uuid.uuid4().hex, "Harry Potter and the Philosopher's Stone", "J. K. Rowling", 0)
    db.session.add(_book)
    _book = Book(uuid.uuid4().hex, "Green Eggs and Ham", "Dr. Seuss", 1)
    db.session.add(_book)
    db.session.commit()