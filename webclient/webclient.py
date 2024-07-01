from flask import Flask
from flask import render_template
from flask import redirect

from .config import webclient as webclient_config

from gtfsgateway.config import app as app_config
from gtfsgateway.gateway import Gateway

class Webclient:

    def __init__(self):
        self._gateway = Gateway(app_config, 'test.yaml')
        self._app = Flask(__name__)

    def _render_template(self, template_name, **args):
        ui_args = dict(
            list(webclient_config['ui'].items()) 
            + list(self._gateway._gateway_config.items())
            + list(args.items())
        )

        return render_template(template_name, **ui_args)

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
        
        return group + " " + function

    def run(self, **args):
        self._app.add_url_rule('/', 'index', self.index)
        self._app.add_url_rule('/fetch', 'fetch', self.fetch)
        self._app.add_url_rule('/process', 'process', self.process)
        self._app.add_url_rule('/publish', 'publish', self.publish)

        self._app.add_url_rule('/ajaxcall/<group>/<function>', 'ajaxcall', self.ajaxcall)

        self._app.jinja_env.auto_reload = True
        self._app.config['TEMPLATES_AUTO_RELOAD'] = True

        self._app.run(**args)

def main():
    webclient = Webclient()
    webclient.run()