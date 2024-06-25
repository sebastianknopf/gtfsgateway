from argparse import ArgumentParser

from .config import app as app_config
from .gateway import Gateway

def main():
    parser = ArgumentParser(prog='cli')
    parser.add_argument('command', help='The command to be run by GTFS gateway')
    parser.add_argument('gatewayconfig', nargs='?', default='gtfsgateway.yaml', help='The yaml file with GTFS gateway configuration')
    args = parser.parse_args()
    
    gateway = Gateway(app_config, args.gatewayconfig)

    if args.command == 'fetch':
        gateway.fetch()
    elif args.command == 'process':
        gateway.process()
    elif args.command == 'publish':
        gateway.publish()
    elif args.command == 'reset':
        gateway.reset()

