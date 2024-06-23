from argparse import ArgumentParser

from .config import app as app_config
from .gateway import Gateway

def main():
    parser = ArgumentParser(prog='cli')
    parser.add_argument('command', help='The command to be run by GTFS gateway')
    parser.add_argument('gatewayconfig', nargs='?', default='gtfsgateway.yaml', help='The yaml file with GTFS gateway configuration')
    args = parser.parse_args()
    
    gateway = Gateway(app_config, args.gatewayconfig)

    if args.command == 'update':
        if gateway.create_data_lock():
            gateway.update_static_feed()
            gateway.run_integration_gtfstidy()
            gateway.load_local_sqlite()

            gateway.release_data_lock()

    elif args.command == 'release':
        if gateway.create_data_lock():
            gateway.create_publish_copy()

            gateway.release_data_lock()

