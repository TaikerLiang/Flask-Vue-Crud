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
        self._history = {}  # file_name: num

    def save(self, to: str, text: str):
        if not to:
            return

        os.makedirs(str(self._folder_path), exist_ok=True)

        new_to = self._check_repeat_and_return_new_name(file_full_name=to)
        to_file = str(self._folder_path / new_to)

        with open(to_file, 'w') as fp:
            fp.write(text)

        self._logger.warning(f'[{self.__class__.__name__}] ----- save file: {to_file}')

    def _check_repeat_and_return_new_name(self, file_full_name: str):
        """
        if file_name already exist
        set file_name to file_name_n, where n = same file_name num
        """
        new_file_full_name = file_full_name
        if file_full_name in self._history:
            file_name, file_type = file_full_name.split('.')
            new_file_full_name = f'{file_name}_{self._history[file_full_name]}.{file_type}'
            self._history[file_full_name] += 1
        else:
            self._history.setdefault(file_full_name, 1)

        return new_file_full_name


class NullSaver(BaseSaver):

    def save(self, to: str, text: str):
        pass
