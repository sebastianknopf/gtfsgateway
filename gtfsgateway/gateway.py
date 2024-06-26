import csv
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

        self.staging_database = StaticDatabase(os.path.join(
            self._app_config['app_directory'],
            self._app_config['staging_filename']
        ))

        clear_directory(self._app_config['tmp_directory'])

    def _create_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        if self._has_data_lock():
            return False
        
        open(local_lock_filename, 'w').close()

        return True

    def _release_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        os.remove(local_lock_filename)

    def _has_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        return os.path.isfile(local_lock_filename)
        
    def _fetch_static_feed(self):
        static_update = self._gateway_config['fetch']['static']['uri']
        destination_file = os.path.join(self._app_config['tmp_directory'], 'fetch.zip')
        
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
                'fetch.zip'
            ),
            '-o',
            self._app_config['tmp_directory']
        ]

        self._run_external_integration('gtfstidy', args)

    def _run_external_integration_gtfsvtor(self):
        static_feed_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['static_feed_filename']
        )

        report_filename = os.path.basename(static_feed_filename)
        report_filename = report_filename.replace('.zip', '')
        report_filename = f"{report_filename}.html"
        
        args = [
            static_feed_filename,
            '-o',
            os.path.join(
                self._app_config['app_directory'], 
                report_filename
            )
        ]
        
        self._run_external_integration('gtfsvtor', args)

    def _load_staging_sqlite(self):
        staging_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['staging_filename']
        )

        staging_backup_filename = os.path.join(
            self._app_config['app_directory'],
            self._app_config['staging_backup_filename']
        )

        # need to close the local database temporary in order to create backup file
        if os.path.isfile(staging_filename):   
            self.staging_database.close()
            
            # remove existing backup in order to create a new one
            if os.path.isfile(staging_backup_filename):
                os.remove(staging_backup_filename)

            os.rename(staging_filename, staging_backup_filename)

            self.staging_database = StaticDatabase(staging_filename)

        # import all existing GTFS files
        self.staging_database.import_csv_files(self._app_config['tmp_directory'])
        clear_directory(self._app_config['tmp_directory'])

    def _create_route_index(self):
        gateway_config_processing_routes = self._gateway_config['processing']['routes']

        route_base_data = self.staging_database.get_route_base_info()
        for route in route_base_data:
            if not any(r['name'] == route['route_short_name'] for r in gateway_config_processing_routes):
                gateway_config_processing_routes.append(
                    dict(
                        name = route[1],
                        id = route[0],
                        include = False
                    )
                )
                
        for i in range(0, len(gateway_config_processing_routes)):
            route = gateway_config_processing_routes[i]
            if not any(r['route_short_name'] == route['name'] for r in route_base_data):
                del gateway_config_processing_routes[i]

        self._gateway_config['processing']['routes'] = gateway_config_processing_routes

        with open(self._gateway_config_filename, 'w') as gateway_config_file:
            yaml.dump(
                self._gateway_config,
                gateway_config_file,
                default_flow_style=False
            )

    def _create_static_database(self):
        static_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['static_filename']
        )
        
        copy_file(
            os.path.join(
                self._app_config['app_directory'], 
                self._app_config['staging_filename']
            ),
            static_filename
        )

        self.static_database = StaticDatabase(static_filename)

    def _load_processing_datafile(self, filename, columns, delimiter=';', quotechar='*'):
        results = list()
        with open(os.path.join(self._app_config['data_directory'], filename), 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=delimiter, quotechar=quotechar)

            for row in csv_reader:
                result = dict()
                for data_col, csv_col in columns.items():
                    result[data_col] = row[csv_col]

                results.append(result)
        
        return results
    
    def _run_processing_functions(self):
        for function in self._app_config['processing']['functions']:
            try:
                module = importlib.import_module(f".processing.{function}", 'gtfsgateway')
                call = getattr(module, function)

                call(self)
            except Exception as ex:
                pass

    def _export_processing_sqlite(self):
        if self.static_database is not None:
            self.static_database.export_csv_files(self._app_config['tmp_directory'])
            self.static_database.close()

            create_zip_file(
                self._app_config['tmp_directory'],
                os.path.join(
                    self._app_config['app_directory'], 
                    self._app_config['static_feed_filename']
                )
            )

            clear_directory(self._app_config['tmp_directory'])

    def _publish_static_feed(self):
        source_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['static_feed_filename']
        )
        
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
            
            with open(source_filename, 'rb') as source_file:
                ftp.storbinary(
                    f"STOR {self._gateway_config['publish']['static']['ftp']['directory']}/{self._gateway_config['publish']['static']['ftp']['filename']}", 
                    source_file
                )

            ftp.quit()

        elif 'filesystem' in self._gateway_config['publish']['static']:
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
                self._load_staging_sqlite()
                self._create_route_index()

                self._release_data_lock()
                self.staging_database.close()

                return True
            except Exception as ex:
                return False
        else:
            return False

    def process(self, **args):
        if self._create_data_lock():
            try:
                self._create_static_database()
                self._run_processing_functions()
                self._export_processing_sqlite()
                self._run_external_integration_gtfsvtor()

                self._release_data_lock()
                self.static_database.close()

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
            