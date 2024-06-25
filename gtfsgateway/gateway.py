import os
import yaml
import importlib
import subprocess
import ftplib

from urllib.request import urlretrieve

from .common.filesystem import clear_directory
from .common.filesystem import copy_file
from .common.filesystem import create_zip_file

from .data.database import StaticDatabase

class Gateway:
    
    def __init__(self, app_config, gateway_config_filename):
        self._app_config = app_config
        
        self._gateway_config_filename = gateway_config_filename
        with open(self._gateway_config_filename) as stream:
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
        
    def _fetch_static_feed(self):
        static_update = self._gateway_config['fetch']['static']['uri']
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

    def _create_route_index(self):
        gateway_config_processing_routes = self._gateway_config['processing']['routes']
        gateway_config_processing_routes = list()

        routes = self._local_database.get_route_base_info()
        for route in routes:
            gateway_config_processing_routes.append({
                'name': route[1],
                'id': route[0],
                'published': False
            })

        self._gateway_config['processing']['routes'] = gateway_config_processing_routes

        with open(self._gateway_config_filename, 'w') as gateway_config_file:
            yaml.dump(
                self._gateway_config,
                gateway_config_file,
                default_flow_style=False
            )

    def _create_processing_database(self):
        processing_database_filename = os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.db3')
        
        copy_file(
            os.path.join(self._app_config['data_directory'], 'gtfsgateway.db3'),
            processing_database_filename
        )

        self._processing_database = StaticDatabase(processing_database_filename)

    def _run_processing_functions(self):
        for function in self._app_config['processing']['functions']:
            module = importlib.import_module(f".processing.{function}", 'gtfsgateway')
            call = getattr(module, function)

            if function == 'remove_routes':
                route_ids = [route['id'] for route in self._gateway_config['processing']['routes'] if route['published'] == False]
                call(self._processing_database, route_ids)
            else:
                call(self._processing_database)

    def _export_processing_sqlite(self):
        if self._processing_database is not None:
            self._processing_database.export_csv_files(self._app_config['tmp_directory'])
            self._processing_database.close()

            os.remove(
                os.path.join(self._app_config['tmp_directory'], 'gtfsgateway.db3')
            )

            create_zip_file(
                self._app_config['tmp_directory'],
                os.path.join(self._app_config['data_directory'], 'gtfsgateway.zip')
            )

            clear_directory(self._app_config['tmp_directory'])

    def _publish_static_feed(self):
        if 'ftp' in self._gateway_config['publish']['static']:
            ftp = ftplib.FTP()

            ftp.connect(
                self._gateway_config['publish']['static']['ftp']['host'],
                self._gateway_config['publish']['static']['ftp']['port']
            )

            ftp.login(
                self._gateway_config['publish']['static']['ftp']['username'],
                self._gateway_config['publish']['static']['ftp']['password']
            )
            
            source_filename = os.path.join(self._app_config['data_directory'], 'gtfsgateway.zip')
            with open(source_filename, 'rb') as source_file:
                ftp.storbinary(
                    f"STOR {self._gateway_config['publish']['static']['ftp']['directory']}/{self._gateway_config['publish']['static']['ftp']['filename']}", 
                    source_file
                )

            ftp.quit()

        elif 'filesystem' in self._gateway_config['publish']['static']:
            source_filename = os.path.join(
                self._app_config['data_directory'],
                'gtfsgateway.zip'
            )

            destination_filename = os.path.join(
                self._gateway_config['publish']['static']['filesystem']['directory'],
                self._gateway_config['publish']['static']['filesystem']['filename']
            )

            os.makedirs(self._gateway_config['publish']['static']['filesystem']['directory'])

            copy_file(source_filename, destination_filename)

    def fetch(self, **args):
        if self._create_data_lock():
            try:
                self._fetch_static_feed()
                self._run_external_integration_gtfstidy()
                self._load_local_sqlite()
                self._create_route_index()

                self._release_data_lock()

                self._local_database.close()

                return True
            except Exception as ex:
                print(ex)
                return False
        else:
            return False

    def process(self, **args):
        if self._create_data_lock():
            try:
                self._create_processing_database()
                self._run_processing_functions()
                self._export_processing_sqlite()
                self._run_external_integration_gtfsvtor()

                self._release_data_lock()
                self._processing_database.close()

                return True
            except Exception as ex:
                return False
        else:
            return False
        
    def publish(self, **args):
        try:
            self._publish_static_feed()
            return True
        except Exception as ex:
            return False
        
    def reset(self, **args):
        if self._has_data_lock():
            self._release_data_lock()

        clear_directory(self._app_config['tmp_directory'])
            