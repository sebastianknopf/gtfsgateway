import click
import time
import logging

from flask import Flask
from flask import render_template
from flask import redirect
from flask import jsonify
from flask import request

from .config import webclient as webclient_config

from .decorators import apiresponse

from gtfsgateway.config import app as app_config
from gtfsgateway.gateway import Gateway

class Webclient:

    def __init__(self, appconfig, gatewayconfig):
        self._gateway = Gateway(app_config, gatewayconfig)
        self._app = Flask(__name__)

    def _render_template(self, template_name, **args):
        ui_args = dict(
            list(webclient_config['ui'].items()) 
            + list(self._gateway._gateway_config.items())
            + list(args.items())
        )

        return render_template(template_name, **ui_args)
        
    def _intersect_gateway_config(self, gateway_config, data):    
        for k, v in data.items():
            if isinstance(v, dict):
                gateway_config[k] = self._intersect_gateway_config(gateway_config[k], v)
            else:
                if k in gateway_config:
                    gateway_config[k] = data[k]
                
        return gateway_config
                
    def _update_gateway_config(self, gateway_config_data):        
        gateway_config = self._gateway._gateway_config
        gateway_config = self._intersect_gateway_config(
            gateway_config, 
            gateway_config_data['data']
        )
        
        self._gateway._update_gateway_config(gateway_config)

    @apiresponse
    def _static_fetch(self, **args):
        request_data = request.json
        self._update_gateway_config(request_data)
        
        result = self._gateway.fetch()
        return (0, 'OK') if result else (500, 'FAIL')
        
    @apiresponse
    def _static_rollback(self, **args):
        return (404, 'Not Implemented')

    @apiresponse
    def _static_process(self, **args):
        request_data = request.json
        
        gateway_config = self._gateway._gateway_config
        route_index = gateway_config['processing']['route_index']
        
        for route in route_index:
            route['include'] = False
        
        for index, data in request_data['data']['processing']['route_index'].items():
            route_index[int(index)]['include'] = data['include']
        
        self._gateway._update_gateway_config(gateway_config)
        
        result = self._gateway.process()
        return (0, 'OK') if result else (500, 'FAIL')

    @apiresponse
    def _static_publish(self, **args):
        return (404, 'Not Implemented')

    def index(self):
        return redirect('fetch', code=303)
    
    def fetch(self):
        return self._render_template('fetch.html')

    def process(self):
        return self._render_template('process.html')

    def publish(self):
        return self._render_template('publish.html')
        
    def status(self):
        return self._render_template('index.html')
        
    def config(self):
        return self._render_template('index.html')
    
    def ajaxcall(self, group, function):
        call_name = f"_{group}_{function}"
        call = getattr(self, call_name)

        result = call()
        return jsonify(result)

    def run(self, **args):
        self._app.add_url_rule('/', 'index', self.index)
        self._app.add_url_rule('/fetch', 'fetch', self.fetch)
        self._app.add_url_rule('/process', 'process', self.process)
        self._app.add_url_rule('/publish', 'publish', self.publish)

        self._app.add_url_rule('/status', 'status', self.status)
        self._app.add_url_rule('/config', 'config', self.config)

        self._app.add_url_rule('/ajaxcall/<group>/<function>', 'ajaxcall', self.ajaxcall, methods=['GET', 'POST'])

        self._app.jinja_env.auto_reload = True
        self._app.config['TEMPLATES_AUTO_RELOAD'] = True

        self._app.run(**args)

@click.command()
@click.option('--gatewayconfig', '-g', default='gtfsgateway.yaml', help='The yaml file with the GTFS gateway configuration')
@click.option('--logfile', '-l', default=None, help='The log filename where GTFS gateway should write logs to')
def main(gatewayconfig, logfile):
    
    if logfile is not None:
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=logfile, level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    
    webclient = Webclient(app_config, gatewayconfig)
    webclient.run()