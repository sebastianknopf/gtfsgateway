import os
import yaml
import subprocess

from urllib.request import urlretrieve

class Gateway:
    
    def __init__(self, config):
        self._config = config
        
        with open(self._config['settings_file']) as stream:
            try:
                self._settings = yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                pass
        
    def download_source_static(self):
        download_url = self._settings['source']['gtfs']['static_download_url']
        destination_file = os.path.join(self._config['tmp_dir'], 'gtfs.zip')
        
        urlretrieve(download_url, destination_file)
        
    def run_external_integration(self, module):
        if module in self._settings['external']['integration']:
            module_bin = os.path.join(self._config['bin_dir'], self._settings['external']['integration']['gtfstidy']['name'])
            if os.path.isfile(module_bin):
                args = (
                    module_bin,
                    self._settings['external']['integration'][module]['args'],
                    os.path.join(self._settings['external']['integration'][module]['working_directory'], 'gtfs.zip'),
                    '-o',
                    self._settings['external']['integration'][module]['working_directory']
                )
            
                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()