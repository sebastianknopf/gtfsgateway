import os
import yaml
import subprocess

from urllib.request import urlretrieve

from .common.filesystem import clear_directory
from .common.filesystem import copy_file
from .common.filesystem import create_zip_file

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

    def _create_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        if self._has_data_lock():
            return False
        
        open(local_lock_filename, 'w').close()

        return True

    def _release_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        os.remove(local_lock_filename)

    def _has_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.lock')
        return os.path.isfile(local_lock_filename)
        
    def _update_static_feed(self):
        static_update = self._gateway_config['source']['static']['update']
        destination_file = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.zip')
        
        if static_update.startswith('http'):
            urlretrieve(static_update, destination_file)
        else:
            copy_file(static_update, destination_file)

    def _run_external_integration(self, module, args):
        if module in self._gateway_config['external']['integration']:
            module_bin = os.path.join(
                self._app_config['bin_directory'], 
                self._gateway_config['external']['integration'][module]['name']
            )

            if os.path.isfile(module_bin):
                module_args = [
                    module_bin,
                    self._gateway_config['external']['integration'][module]['args']
                ]
                module_args = module_args + args

                popen = subprocess.Popen(' '.join(module_args), stdout=subprocess.PIPE)
                popen.wait()
        
    def _run_external_integration_gtfstidy(self):
        args = [
            os.path.join(
                self._app_config['tmp_directory'], 
                'gtfsgateway.zip'
            ),
            '-o',
            self._app_config['tmp_directory']
        ]

        self._run_external_integration('gtfstidy', args)

    def _run_external_integration_gtfsvtor(self):
        args = [
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.zip'),
            '-o',
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.html')
        ]
        
        self._run_external_integration('gtfsvtor', args)

    def _load_local_sqlite(self):
        local_database_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3')
        local_backup_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.bak')

        # need to close the local database temporary in order to create backup file
        if os.path.isfile(local_database_filename):   
            self._local_database.close()
            
            os.rename(local_database_filename, local_backup_filename)

            self._local_database = StaticDatabase(local_database_filename)

        # import all existing GTFS files
        self._local_database.import_csv_files(self._app_config['tmp_directory'])

        clear_directory(self._app_config['tmp_directory'])

        # remove backup since import worked properly
        if os.path.isfile(local_backup_filename):
            os.remove(local_backup_filename)

    def _create_release_database(self):
        release_database_filename = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.db3')
        
        copy_file(
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3'),
            release_database_filename
        )

        self._release_database = StaticDatabase(release_database_filename)

    def _export_release_sqlite(self):
        if self._release_database is not None:
            self._release_database.export_csv_files(self._app_config['tmp_directory'])
            self._release_database.close()

            os.remove(
                os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.db3')
            )

            create_zip_file(
                self._app_config['tmp_directory'],
                os.path.join(self._app_config['data_directory'], 'gtfsgateway.zip')
            )

            clear_directory(self._app_config['tmp_directory'])

    def update(self, **args):
        if self._create_data_lock():
            try:
                self._update_static_feed()
                self._run_external_integration_gtfstidy()
                self._load_local_sqlite()

                self._release_data_lock()
                self._local_database.close()

                return True
            except Exception as ex:
                print(ex)
                return False
        else:
            return False

    def release(self, **args):
        if self._create_data_lock():
            try:
                self._create_release_database()

                self._export_release_sqlite()

                self._run_external_integration_gtfsvtor()

                self._release_data_lock()
                self._release_database.close()

                return True
            except Exception as ex:
                return False
        else:
            return False
            