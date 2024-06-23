import os
import yaml
import subprocess

from urllib.request import urlretrieve

from .common.filesystem import clear_directory
from .common.filesystem import copy_file
from .data.database import StaticDatabase

class Gateway:
    
    def __init__(self, app_config, gateway_config_filename):
        self._app_config = app_config
        
        with open(gateway_config_filename) as stream:
            try:
                self._gateway_config = yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                print(ex)

        self._local_database = StaticDatabase(os.path.join(
            self._app_config['data_directory'],
            'gtfsgateway.db3'
        ))

        clear_directory(self._app_config['tmp_directory'])

    def create_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        if self.has_data_lock():
            return False
        
        open(local_lock_filename, 'w').close()

        return True

    def release_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        os.remove(local_lock_filename)

    def has_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        return os.path.isfile(local_lock_filename)
        
    def update_static_feed(self):
        static_update = self._gateway_config['source']['static']['update']
        destination_file = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.zip')
        
        if static_update.startswith('http'):
            urlretrieve(static_update, destination_file)
        else:
            copy_file(static_update, destination_file)
        
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
                        self._app_config['tmp_directory'], 
                        'gtfsgateway.zip'
                    ),
                    '-o',
                    self._app_config['tmp_directory']
                )
            
                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()

    def load_local_sqlite(self):
        local_database_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3')
        local_backup_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.bak')

        # need to close the local database temporary in order to create backup file
        if os.path.isfile(local_database_filename):   
            self._local_database.close()
            
            os.rename(local_database_filename, local_backup_filename)

            self._local_database = StaticDatabase(local_database_filename)

        # import all existing GTFS files
        for f in os.listdir(self._app_config['tmp_directory']):
            if f.endswith('.txt'):
                table_name = f.replace('.txt', '')
                file_name = os.path.join(self._app_config['tmp_directory'], f)

                self._local_database.import_csv_file(file_name, table_name)

        clear_directory(self._app_config['tmp_directory'])

        # remove backup since import worked properly
        if os.path.isfile(local_backup_filename):
            os.remove(local_backup_filename)

    def create_release_database(self):
        release_database_filename = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.db3')
        
        copy_file(
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3'),
            release_database_filename
        )

        self._release_database = StaticDatabase(release_database_filename)