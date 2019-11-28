from locust import HttpLocust, TaskSet, task
from locust.exception import StopLocust
from pprint import pprint
import random
import json


class WebsiteTasks(TaskSet):
    @task(10)
    def index(self):
        self.client.get("/ping")

    @task(3)
    def get_books(self):
        self.client.get("/books")
    
    @task(1)
    def post_books(self):
        data = {"title": "Python3", "author": "Paul Liang", "read": False}
        self.client.post("/books", data=json.dumps(data))

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    min_wait = 5000
    max_wait = 9000
