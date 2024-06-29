from flask import Flask
from flask import render_template
from flask import redirect

from .config import config as app_config

class Webclient:

    def __init__(self):
        self._app = Flask(__name__)

    def _render_template(self, template_name, **args):
        ui_args = dict(list(app_config['ui'].items()) + list(args.items()))

        return render_template(template_name, **ui_args)

    def index(self):
        return redirect('fetch', code=303)
    
    def fetch(self):
        return self._render_template('index.html')

    def process(self):
        return self._render_template('index.html')

    def publish(self):
        return self._render_template('index.html')
    
    def ajaxcall(self):
        pass

    def run(self, **args):
        self._app.add_url_rule('/', 'index', self.index)
        self._app.add_url_rule('/fetch', 'fetch', self.fetch)
        self._app.add_url_rule('/process', 'process', self.process)
        self._app.add_url_rule('/publish', 'publish', self.publish)

        self._app.add_url_rule('/ajaxcall/<function>', 'ajaxcall', self.ajaxcall)

        self._app.run(**args)

def main():
    webclient = Webclient()
    webclient.run()