import click
import logging

from .config import app as app_config
from .gateway import Gateway

@click.command()
@click.argument('command')
@click.option('--gatewayconfig', '-g', default='gtfsgateway.yaml', help='The yaml file with the GTFS gateway configuration')
@click.option('--logfile', '-l', default=None, help='The log filename where GTFS gateway should write logs to')
def main(command, gatewayconfig, logfile):
    gateway = Gateway(app_config, gatewayconfig)

    if logfile is not None:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=logfile, level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    if command == 'fetch':
        gateway.fetch()
    elif command == 'process':
        gateway.process()
    elif command == 'publish':
        gateway.publish()
    elif command == 'reset':
        gateway.reset()

