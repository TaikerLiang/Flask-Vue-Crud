import abc
import os
from pathlib import Path


class BaseSaver:

    @abc.abstractmethod
    def save(self, to: str, text: str):
        pass


class FileSaver(BaseSaver):

    def __init__(self, folder_path: Path, logger):
        self._folder_path = folder_path
        self._logger = logger

    def save(self, to: str, text: str):
        if not to:
            return

        os.makedirs(str(self._folder_path), exist_ok=True)

        to_file = str(self._folder_path / to)

        with open(to_file, 'w') as fp:
            fp.write(text)

        self._logger.warning(f'[{self.__class__.__name__}] ----- save file: {to_file}')


class NullSaver(BaseSaver):

    def save(self, to: str, text: str):
        pass
