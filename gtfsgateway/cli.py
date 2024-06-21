from argparse import ArgumentParser

from .config import app as app_config
from .gateway import Gateway

def main():
    parser = ArgumentParser(prog='cli')
    parser.add_argument('command', help='The command to be run by GTFS gateway')
    args = parser.parse_args()
    
    gateway = Gateway(app_config)

    if args.command == 'update':
        gateway.download_source_static()
        gateway.run_integration_gtfstidy()
        gateway.load_local_sqlite()

    elif args.command == 'finalize':
        pass

