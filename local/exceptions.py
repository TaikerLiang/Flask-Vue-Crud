class LoadWebsiteTimeOut(Exception):
    pass


class DataNotFoundError(Exception):
    def __init__(self, task_id):
        self._task_id = task_id

    @property
    def task_id(self):
        return self._task_id


class AccessDeniedError(Exception):
    pass
