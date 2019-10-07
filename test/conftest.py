import importlib
from pathlib import Path

import pytest


@pytest.fixture
def sample_loader():

    class _Loader:

        def __init__(self):
            self.sample_package = None
            self.sample_path = None

        def setup(self, sample_package, sample_path: Path):
            self.sample_package = sample_package
            self.sample_path = sample_path.absolute()

            pytest.register_assert_rewrite(sample_package.__name__)

        def load_sample_module(self, *module_names: str):
            return importlib.import_module(f'.{".".join(module_names)}', package=self.sample_package.__name__)

        def build_file_path(self, *path_list: str) -> Path:
            return self.sample_path / Path(*path_list)

        def read_file(self, *path_list: str) -> str:
            file_path = self.build_file_path(*path_list)
            with open(str(file_path), 'r') as fp:
                text = fp.read()
            return text

    return _Loader()
