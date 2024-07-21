import csv
import os
import yaml
import importlib
import subprocess
import ftplib
import logging
import pysftp 

from urllib.request import urlretrieve

from .common.filesystem import clear_directory
from .common.filesystem import copy_file
from .common.filesystem import create_zip_file

from .data.database import StaticDatabase

class Gateway:
    
    def __init__(self, app_config, gateway_config_filename):
        self._app_config = app_config
        
        self._gateway_config_filename = gateway_config_filename
        with open(self._gateway_config_filename, mode='r', encoding='utf-8') as stream:
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
        logging.info('creating data lock file')
        
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        if self._has_data_lock():
            return False
        
        open(local_lock_filename, 'w').close()

        return True

    def _release_data_lock(self):
        logging.info('remove data lock file')
        
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        os.remove(local_lock_filename)

    def _has_data_lock(self):
        local_lock_filename = os.path.join(self._app_config['app_directory'], 'gtfsgateway.lock')
        return os.path.isfile(local_lock_filename)
    
    def _update_gateway_config(self, gateway_config):
        self._gateway_config = gateway_config
    
        with open(self._gateway_config_filename, mode='w', encoding='utf-8') as gateway_config_file:
            yaml.dump(
                gateway_config,
                gateway_config_file,
                default_flow_style=False,
                sort_keys=False
            )
        
    def _fetch_static_feed(self):
        fetch_static_config = self._gateway_config['fetch']['static']
        destination_file = os.path.join(self._app_config['tmp_directory'], 'fetch.zip')
        
        fetch_source = fetch_static_config['source']

        if fetch_source == 'remote' and fetch_source in fetch_static_config:
            logging.info('fetching static from remote')
            urlretrieve(fetch_static_config['remote']['url'], destination_file)
        elif fetch_source == 'filesystem' and fetch_source in fetch_static_config:
            logging.info('fetching static feed from filesystem')
            copy_file(fetch_static_config['filesystem']['filename'], destination_file)            

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

                logging.info(f"parameters {module_args}")

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

        logging.info(f"running external integration for gtfstidy")

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

        logging.info(f"running external integration for gtfsvtor")
        
        self._run_external_integration('gtfsvtor', args)

    def _create_staging_database(self):
        logging.info('creating staging database')
        
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
            logging.info('creating backup of staging database')

            self.staging_database.close()
            
            # remove existing backup in order to create a new one
            if os.path.isfile(staging_backup_filename):
                os.remove(staging_backup_filename)

            os.rename(staging_filename, staging_backup_filename)

            self.staging_database = StaticDatabase(staging_filename)

        # import all existing GTFS files
        logging.info(f"importing files from {self._app_config['tmp_directory']}")

        self.staging_database.import_csv_files(self._app_config['tmp_directory'])
        clear_directory(self._app_config['tmp_directory'])
        
    def _rollback_staging_database(self):
        logging.info('rolling back staging database')
        
        staging_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['staging_filename']
        )

        staging_backup_filename = os.path.join(
            self._app_config['app_directory'],
            self._app_config['staging_backup_filename']
        )
        
        if os.path.isfile(staging_filename) and os.path.isfile(staging_backup_filename):
            # close, rename and reconnect to the staging database
            self.staging_database.close()
            
            os.remove(staging_filename)
            copy_file(staging_backup_filename, staging_filename)
            
            self.staging_database = StaticDatabase(staging_filename)
        else:
            raise Exception('either staging database or staging backup is not available') 

    def _create_route_index(self):
        logging.info('creating route index')

        gateway_config_processing_routes = self._gateway_config['processing']['route_index']

        route_base_data = self.staging_database.get_route_base_info()
        for route in route_base_data:
            if not any(r['name'] == route['route_short_name'] and r['id'] == route['route_id'] for r in gateway_config_processing_routes):
                logging.info(f"creating route entry for {route['route_short_name']} ({ route['route_id']})")
                
                gateway_config_processing_routes.append(
                    dict(
                        name = route['route_short_name'],
                        id = route['route_id'],
                        include = False
                    )
                )

        updated_processing_routes = list(gateway_config_processing_routes)        
        for i in range(0, len(gateway_config_processing_routes)):
            route = gateway_config_processing_routes[i]
            if not any(r['route_short_name'] == route['name'] for r in route_base_data):
                logging.info(f"removing route entry for {route['name']} ({ route['id']})")

                del updated_processing_routes[i]

        gateway_config_processing_routes = updated_processing_routes

        self._gateway_config['processing']['route_index'] = gateway_config_processing_routes

        self._update_gateway_config(self._gateway_config)

    def _create_static_database(self):
        logging.info('creating static database')

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
        datafile_filename = os.path.join(self._app_config['data_directory'], filename)
        
        logging.info(f"loading processing data file {datafile_filename}")
        
        results = list()
        with open(datafile_filename, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=delimiter, quotechar=quotechar)

            for row in csv_reader:
                result = dict()
                for data_col, csv_col in columns.items():
                    result[data_col] = row[csv_col]

                results.append(result)
        
        return results
    
    def _run_processing_functions(self):
        for function in self._gateway_config['processing']['functions']:
            try:
                if function['active']:
                    logging.info(f"running processing function {function['name']}")

                    module = importlib.import_module(f".processing.{function['name']}", 'gtfsgateway')
                    call = getattr(module, function['name'])

                    if 'params' in function:
                        call(self, function['params'])
                    else:
                        call(self, dict())
            except Exception as ex:
                logging.error(f"error executing function {function['name']}")
                logging.exception(ex)

    def _export_static_database(self):
        if self.static_database is not None:
            logging.info('exporting static database')

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
        publish_static_config = self._gateway_config['publish']['static']

        source_filename = os.path.join(
            self._app_config['app_directory'], 
            self._app_config['static_feed_filename']
        )
        
        publish_destination = publish_static_config['destination']
        
        if publish_destination == 'ftp' and publish_destination in publish_static_config:
            logging.info('publishing static feed to ftp')

            ftp = ftplib.FTP()

            ftp.connect(
                publish_static_config['ftp']['host'],
                int(publish_static_config['ftp']['port'])
            )

            ftp.login(
                publish_static_config['ftp']['username'],
                publish_static_config['ftp']['password']
            )
            
            with open(source_filename, 'rb') as source_file:
                ftp.storbinary(
                    f"STOR {publish_static_config['ftp']['directory']}/{publish_static_config['ftp']['filename']}", 
                    source_file
                )

            ftp.quit()
            
        elif publish_destination == 'sftp' and publish_destination in publish_static_config:
            logging.info('publishing static feed to sftp')
            
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            
            sftp = pysftp.Connection(
                host=publish_static_config['sftp']['host'],
                username=publish_static_config['sftp']['username'],
                password=publish_static_config['sftp']['password'],
                port=int(publish_static_config['sftp']['port']),
                cnopts=cnopts
            )
            
            sftp.put(source_filename, os.path.join(
                publish_static_config['sftp']['directory'],
                publish_static_config['sftp']['filename']
            ))
            
            sftp.close()

        elif publish_destination == 'filesystem' and publish_destination in publish_static_config:
            logging.info('publishing static feed to filesystem')

            destination_filename = os.path.join(
                publish_static_config['filesystem']['directory'],
                publish_static_config['filesystem']['filename']
            )

            if not os.path.isdir(publish_static_config['filesystem']['directory']):
                os.makedirs(publish_static_config['filesystem']['directory'])

            copy_file(source_filename, destination_filename)

    def fetch(self, **args):
        if self._create_data_lock():
            logging.info('running fetch command')

            try:
                self._fetch_static_feed()
                self._run_external_integration_gtfstidy()
                self._create_staging_database()
                self._create_route_index()

                self._release_data_lock()
                self.staging_database.close()

                return True
            except Exception as ex:
                logging.error('error executing fetch command')
                logging.exception(ex)
                return False
        else:
            return False

    def process(self, **args):
        if self._create_data_lock():
            logging.info('running process command')

            try:
                self._create_static_database()
                self._run_processing_functions()
                self._export_static_database()
                self._run_external_integration_gtfsvtor()

                self._release_data_lock()
                self.static_database.close()

                return True
            except Exception as ex:
                logging.error('error executing process command')
                logging.exception(ex)
                return False
        else:
            return False
        
    def publish(self, **args):
        logging.info('running publish command')

        try:
            self._publish_static_feed()
            return True
        except Exception as ex:
            logging.error('error executing publish command')
            logging.exception(ex)
            return False
            
    def rollback(self, **args):
        if self._create_data_lock():
            logging.info('running rollback command')
            
            try:
                self._rollback_staging_database()
                
                self._release_data_lock()
                self.staging_database.close()
                
                return True
            except Exception as ex:
                logging.error('error executing rollback command')
                logging.exception(ex)
                return False
        
    def reset(self, **args):
        logging.info('running reset command')

        if self._has_data_lock():
            self._release_data_lock()

        clear_directory(self._app_config['tmp_directory'])
            