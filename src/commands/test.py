from pathlib import Path

import click
import pytest


ROOT = Path(__file__).parent.parent.parent

DEFAULT_TARGET = str(ROOT / 'test')


@click.command()
@click.option('--target', default=DEFAULT_TARGET, help='target to test')
@click.option('--pytest-args', 'pytest_args', default='', help='args pass to pytest')
def cli(target, pytest_args):
    click.echo(f'Test: {target}')

    extra_args = pytest_args.split(' ')

    args = [
        '-x',
        target,
        *extra_args,
    ]

    pytest.main(args)
