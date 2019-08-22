"""
.. module:: books
   :platform: Ubuntu 18.04, linux & Mac OS
   :synopsis: restful api of books

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""

from flask import jsonify, redirect, request, abort, make_response
from flask_restful import Resource, Api
from src.models.books import Book
from src import app, db
from pprint import pprint
import json
import datetime
import uuid

api = Api(app)

BOOKS = [
    {
        "id": uuid.uuid4().hex,
        "title": "On the Road",
        "author": "Jack Kerouac",
        "read": True,
    },
    {
        "id": uuid.uuid4().hex,
        "title": "Harry Potter and the Philosopher's Stone",
        "author": "J. K. Rowling",
        "read": False,
    },
    {
        "id": uuid.uuid4().hex,
        "title": "Green Eggs and Ham",
        "author": "Dr. Seuss",
        "read": True,
    },
]


class RBooks(Resource):
    """
    @apiDefine UnauthorizedError
    @apiError 401 Unauthorized: Access is denied due to invalid credentials
    @apiErrorExample Error-Response:
    HTTP/1.1 401 Unauthorized
    {
        "error": "Unauthorized: Access is denied due to invalid credentials."
    }
    """

    def get(self):
        """
        @api {get} /books get books info
        @apiVersion 1.0.0
        @apiName get_books
        @apiGroup Books
        @apiSuccess {Array}    books             list of book object
        @apiSuccess {String}   status            status of request
        @apiSuccess {String}   id                id of book
        @apiSuccess {String}   author            author of book
        @apiSuccess {String}   title             title of book
        @apisuccess {Boolean}  read              read this book or not
        @apiSuccessExample {Json} Success-Response:
        HTTP/1.1 200 OK
        {
            'books': [
                {
                    'author': 'Jack Kerouac', 
                    'id': '0e07890f1d884789ad7990de01bbbab8', 
                    'read': True, 
                    'title': 'On the Road'
                }, 
                {
                    'author': 'J. K. Rowling', 
                    'id': '3350bb1b80ea42eb9686ff7d5f940ac5', 
                    'read': False, 
                    'title': "Harry Potter and the Philosopher's Stone"
                }, 
                {
                    'author': 'Dr. Seuss', 
                    'id': '3d4bad38997b4481b90efbee4d1921fd', 
                    'read': True, 
                    'title': 'Green Eggs and Ham'
                }
            ], 
            'status': 'success'
        }
        """
        def __process_return_value(obj):
            tmp = dict()
            tmp["id"] = obj.book_id
            tmp["title"] = obj.title
            tmp["author"] = obj.author
            tmp["read"] = obj.read
            return tmp

        res = dict()
        res["status"] = "success"
        res["books"] = list()
        _books = Book.query.all()
        for r in _books:
            tmp = __process_return_value(r)
            res["books"].append(tmp)
            print(tmp)
        
        return jsonify(res)

    def post(self):
        """
        @api {post} /books add a book
        @apiVersion 1.0.0
        @apiName add_books
        @apiGroup Books
        @apiParam {String}   author            author of book
        @apiParam {String}   title             title of book
        @apiParam {Boolean}  read              read this book or not
        @apiParamExample {json} Request-Example:
        {
            'title': 'Python3',
            'author': 'Paul Liang',
            'read': False,
        }
        @apiSuccess {String}   status             status of request
        @apiSuccess {String}   message            message for showing to user
        @apiSuccessExample {Json} Success-Response:
        HTTP/1.1 200 OK
        {
            'message': 'Book added!',
            'status': 'success'
        }
        """
        req_data = request.get_json(force=True)

        try:
            _title = req_data["title"]
            _author = req_data["author"]
            _read = req_data["read"]

            _book = Book(uuid.uuid4().hex, _title, _author, _read)
            db.session.add(_book)
            db.session.commit()
            return make_response(jsonify({"status": "success", "message": "Book added!"}), 200)
        except:
            return make_response(
                jsonify({"status": "failed", "message": "miss some parameters"}), 400
            )

    def put(self, book_id):
        """
        @api {put} /books update a book info
        @apiVersion 1.0.0
        @apiName edit_books
        @apiGroup Books
        """
        response_object = {"status": "success"}
        req_data = request.get_json()
        try:
            _title = req_data["title"]
            _author = req_data["author"]
            _read = req_data["read"]
        except:
            return make_response(
                jsonify({"status": "failed", "message": "miss some parameters"}), 400
            )

        _book = Book.query.filter(Book.book_id == book_id).first()

        if _book:
            _book.title = _title
            _book.author = _author
            _book.read = _read

            db.session.commit()

        return make_response(jsonify({"status": "success", "message": "Book updated!"}), 200)

    def delete(self, book_id):
        """
        @api {delete} /books delete a book
        @apiVersion 1.0.0
        @apiName deleete_books
        @apiGroup Books
        """

        try:
            _book = Book.query.filter(Book.book_id == book_id).first()
            db.session.delete(_book)
            db.session.commit()
            return make_response(jsonify({"status": "success", "message": "Book updated!"}), 200)
        except:
            return make_response(
                jsonify({"status": "failed", "message": "something wrong"}), 400
            )


api.add_resource(RBooks, "/books", endpoint="/books")
api.add_resource(RBooks, "/books/<string:book_id>", endpoint="/books/book_id")
