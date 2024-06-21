from argparse import ArgumentParser

from .config import app

from .gateway import Gateway

def main():
    parser = ArgumentParser(prog='cli')
    parser.add_argument('command', help='The command to be run by GTFS gateway')
    args = parser.parse_args()
    
    gateway = Gateway(app)
    gateway.download_source_static()
    gateway.run_external_integration('gtfstidy')