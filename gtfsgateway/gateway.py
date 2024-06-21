import os
import yaml
import subprocess

from urllib.request import urlretrieve

from .common.filesystem import clear_directory
from .data.database import LocalDatabase

class Gateway:
    
    def __init__(self, app_config):
        self._app_config = app_config
        
        with open(self._app_config['gateway_config_file']) as stream:
            try:
                self._gateway_config = yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                pass

        self._local_database = LocalDatabase(os.path.join(
            self._app_config['data_directory'],
            'gtfsgateway.db3'
        ))

        clear_directory(self._app_config['tmp_directory'])
        
    def download_source_static(self):
        download_url = self._gateway_config['source']['gtfs']['static_download_url']
        destination_file = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.zip')
        
        urlretrieve(download_url, destination_file)
        
    def run_integration_gtfstidy(self):
        if 'gtfstidy' in self._gateway_config['external']['integration']:
            module_bin = os.path.join(
                self._app_config['bin_directory'], 
                self._gateway_config['external']['integration']['gtfstidy']['name']
            )

            if os.path.isfile(module_bin):
                args = (
                    module_bin,
                    self._gateway_config['external']['integration']['gtfstidy']['args'],
                    os.path.join(
                        self._gateway_config['external']['integration']['gtfstidy']['working_directory'], 
                        'gtfsgateway.zip'
                    ),
                    '-o',
                    self._gateway_config['external']['integration']['gtfstidy']['working_directory']
                )
            
                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()

    

    def load_local_sqlite(self):
        # need to close the local database temporary in order to create backup file
        self._local_database.close()
        
        os.rename(
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3'),
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.bak')
        )

        self._local_database = LocalDatabase(os.path.join(
            self._app_config['data_directory'],
            'gtfsgateway.db3'
        ))

        # import all existing GTFS files
        for f in os.listdir(self._app_config['tmp_directory']):
            if f.endswith('.txt'):
                table_name = f.replace('.txt', '')
                file_name = os.path.join(self._app_config['tmp_directory'], f)

                self._local_database.import_csv_file(file_name, table_name)

        clear_directory(self._app_config['tmp_directory'])

        os.remove(
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.bak')
        )