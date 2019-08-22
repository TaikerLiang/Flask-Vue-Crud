"""
.. module: books
   :platform: Ubuntu 18.04, linux & Mac OS
   :synopsis: mapping to books table in database

.. moduleauthor:: Paul Liang <liang0816tw@gmailc.om>
.. date:: 2019-08-21
"""

from src import app
from src import db
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    ARRAY,
    SmallInteger,
)
from pprint import pprint
import datetime


class Book(db.Model):

    __tablename__ = "books"

    # table columns
    id = Column(Integer, primary_key=True)
    book_id = Column(String)
    title = Column(String)
    author = Column(String)
    read = Column(SmallInteger)
    created_time = Column(DateTime)

    def __init__(self, book_id, title, author, read):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.read = read
        self.created_time = datetime.datetime.now()
