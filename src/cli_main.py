import click
import importlib
import inspect
import pkgutil

import commands


def is_click_command(obj):
    return isinstance(obj, click.core.Command)


class CliFactory:
    @staticmethod
    def build_from_package(pkg):
        inst = click.Group()

        for module_info in pkgutil.iter_modules(path=pkg.__path__):
            module_name = module_info.name
            full_module_name = f'{pkg.__name__}.{module_name}'
            module = importlib.import_module(full_module_name)

            command_members = inspect.getmembers(module, predicate=is_click_command)
            for name, cmd_inst in command_members:
                if name == 'cli':
                    cmd_name = module_name
                else:
                    cmd_name = f'{module_name}.{name}'

                inst.add_command(cmd_inst, cmd_name)

        return inst


cli = CliFactory.build_from_package(commands)


if __name__ == '__main__':
    cli()
