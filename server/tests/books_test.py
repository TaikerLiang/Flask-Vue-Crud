"""
.. module:: books_test
   :platform: Ubuntu 18.04, linux & Mac OS
   :synopsis: unit test of src/books.py

.. moduleauthor:: Paul Liang <liang0816tw@gmail.com>
.. date:: 2019-07-07
"""
from pprint import pprint
import json
import pytest


def test_get(app_client, books):

    response = app_client.get("/books", content_type="application/json")
    res = json.loads(response.get_data(as_text=True))
    print(res)
    assert response.status_code == 200
    assert len(res["books"]) == 3


def test_post(app_client):

    data = {"title": "Python3", "author": "Paul Liang", "read": 0}

    response = app_client.post(
        "/books", data=json.dumps(data), content_type="application/json"
    )
    print(json.loads(response.get_data(as_text=True)))
    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert res["message"] == "Book added!"

    response = app_client.get("/books", content_type="application/json")
    res = json.loads(response.get_data(as_text=True))
    print(res)
    assert response.status_code == 200
    assert len(res["books"]) == 4


def test_put(app_client):

    response = app_client.get("/books", content_type="application/json")
    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    book_id = res["books"][0]["id"]
    data = {"title": "Python3 for beginner", "author": "Paul Liang", "read": 1}

    response = app_client.put(
        "/books/" + str(book_id), data=json.dumps(data), content_type="application/json"
    )

    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200


def test_delete(app_client):
    
    response = app_client.get("/books", content_type="application/json")
    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    book_id = res["books"][0]["id"]

    response = app_client.delete(
        "/books/" + str(book_id), content_type="application/json"
    )

    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200

    response = app_client.get("/books", content_type="application/json")
    res = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert len(res["books"]) == 3
