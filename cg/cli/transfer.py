# -*- coding: utf-8 -*-
import click

from cg.apps.stats import StatsAPI
from cg.meta import transfer as transfer_app
from cg.store import Store


@click.group()
@click.pass_context
def transfer(context):
    """Transfer results to the status interface."""
    context.obj['db'] = Store(context.obj['database'])


@transfer.command()
@click.argument('flowcell')
@click.pass_context
def flowcell(context, flowcell):
    """Populate results from a flowcell."""
    stats_api = StatsAPI(context.obj)
    new_record = transfer_app.flowcell(context.obj['db'], stats_api, flowcell)
    context.obj['db'].add_commit(new_record)
    click.echo(click.style(f"flowcell added: {new_record}", fg='green'))