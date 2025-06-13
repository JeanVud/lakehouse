import click

@click.group()
@click.option('--log-level', default="DEBUG")
@click.option('--dry-run/--no-dry-run', default=False)
@click.pass_context
def cli(ctx, log_level, dry_run):
  """Vultr CLI Tool"""
  pass


@click.group(name='migrate')
def migration_tools():
  """Data Lake related operation commands"""
  pass

@migration_tools.command(name='sync-one', help='sync table from Big Query')
def print_hello():
    """Prints hello world"""
    print("Hello, world!")

@migration_tools.command(name='sync-one2', help='sync table from Big Query')
def print_hello2():
    """Prints hello world"""
    print("Hello, world!")

if __name__ == '__main__':
  cli.add_command(migration_tools)
  cli()