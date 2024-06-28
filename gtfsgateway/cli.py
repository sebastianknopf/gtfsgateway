import click

from .config import app as app_config
from .gateway import Gateway

@click.command()
@click.argument('command')
@click.option('--gatewayconfig', '-g', default='gtfsgateway.yaml', help='The yaml file with the GTFS gateway configuration')
def main(command, gatewayconfig):
    gateway = Gateway(app_config, gatewayconfig)

    if command == 'fetch':
        gateway.fetch()
    elif command == 'process':
        gateway.process()
    elif command == 'publish':
        gateway.publish()
    elif command == 'reset':
        gateway.reset()

