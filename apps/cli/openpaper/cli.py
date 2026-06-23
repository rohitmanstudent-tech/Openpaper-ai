"""OpenPaper Hub CLI — main entry point."""

import sys
import click

from openpaper import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="openpaper")
@click.pass_context
def main(ctx: click.Context):
    """OpenPaper Hub CLI — search, install, publish, and manage packages.

    \b
    Examples:
        openpaper search export
        openpaper install export-agent
        openpaper install sales-agent@1.1.0
        openpaper publish ./my-agent/
        openpaper unpublish my-agent
        openpaper login
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Import commands to register them
from openpaper.commands.search import search  # noqa: E402, F401
from openpaper.commands.install import install  # noqa: E402, F401
from openpaper.commands.publish import publish  # noqa: E402, F401
from openpaper.commands.unpublish import unpublish  # noqa: E402, F401
from openpaper.commands.login import login, logout, whoami  # noqa: E402, F401


main.add_command(search)
main.add_command(install)
main.add_command(publish)
main.add_command(unpublish)
main.add_command(login)
main.add_command(logout)
main.add_command(whoami)


if __name__ == "__main__":
    main()
