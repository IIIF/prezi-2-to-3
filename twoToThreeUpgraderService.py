#!/usr/bin/env python
# encoding: utf-8
"""IIIF Presentation Validation Service"""

import argparse
import json
import os
import sys
try:
    # python3
    from urllib.request import urlopen, HTTPError
    from urllib.parse import urlparse
except ImportError:
    # fall back to python2
    from urllib2 import urlopen, HTTPError
    from urlparse import urlparse

from bottle import Bottle, abort, request, response, run, template

#egg_cache = "/path/to/web/egg_cache"
#os.environ['PYTHON_EGG_CACHE'] = egg_cache

from iiif_prezi_upgrader import Upgrader
from iiif_prezi_upgrader.prezi_upgrader import FLAGS

class Service(object):

    def __init__(self):
        self.default_flags = {}

    def fetch(self, url):
        try:
            wh = urlopen(url)
        except HTTPError as wh:
            pass
        data = wh.read()
        wh.close()
        try:
            data = data.decode('utf-8')
        except:
            pass
        return (data, wh)

    def return_json(self, js):
        response.content_type = "application/json"
        return json.dumps(js)

    def do_upgrade(self, js, flags={}):
        up = Upgrader(flags=flags)
        results = up.process_resource(js, top=True)
        return self.return_json(results)

    def do_POST_upgrade(self):
        data = request.json
        if not data:
            b = request._get_body_string()
            try:
                b = b.decode('utf-8')
            except:
                pass
            data = json.loads(b)
        return self.do_upgrade(data)

    def do_GET_upgrade(self):
        url = request.query.get('url', '')
        url = url.strip()
        parsed_url = urlparse(url)
        if not parsed_url.scheme.startswith('http'):
            return self.return_json({'okay': 0, 'error': 'URLs must use HTTP or HTTPS', 'url': url})
        try:
            (data, webhandle) = self.fetch(url)
        except:
            return self.return_json({'okay': 0, 'error': 'Cannot fetch url', 'url': url})

        # catch if this is invalid JSON e.g. using a non IIIF resoruces like www.google.com
        try:
            data = json.loads(data)
        except TypeError as error:
            return self.return_json({'okay': 0, 'error': 'Invalid JSON for supplied url.', 'url': url, 'json_error': str(error)})

        # And look for flags
        fs = FLAGS
        flags = {}
        for f in fs:
            if request.query.get(f, None):
                val = request.query[f]
                if val == "True":
                    val = True
                elif val == "False":
                    val = False
                flags[f] = val

        try:
            response = self.do_upgrade(data, flags)
        except Exception, e:
            response = {'okay': 0, 'error': "Error: %s" % e }
        return response

    def index_route(self):
        output = template('templates/index.tpl', flags=FLAGS)
        return output

    def dispatch_views(self):
        self.app.route("/", "GET", self.index_route)
        self.app.route("/upgrade", "OPTIONS", self.empty_response)
        self.app.route("/upgrade", "GET", self.do_GET_upgrade)
        self.app.route("/upgrade", "POST", self.do_POST_upgrade)

    def after_request(self):
        methods = 'GET,POST,OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods

    def empty_response(self, *args, **kwargs):
        """Empty response"""

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        return self.app

def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--hostname', default='localhost',
                        help='Hostname or IP address to bind to (use 0.0.0.0 for all)')
    parser.add_argument('--port', default=8080, type=int,
                        help='Server port to bind to. Values below 1024 require root privileges.')

    args = parser.parse_args()

    s = Service()
    run(host=args.hostname, port=args.port, app=s.get_bottle_app())

if __name__ == "__main__":
    main()
else:
    s = Service()
    application = s.get_bottle_app()
