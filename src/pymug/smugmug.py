# -*- coding: utf-8 -*-
# Copyright (c) 2009-2011 Erik Karulf <erik@karulf.com> - MIT License
__version__ = "0.2"

API_VERSION='1.2.2'
API_DOMAIN='api.smugmug.com'
API_DOMAIN_SSL='secure.smugmug.com'
API_KEY='WqITE8jW2WvhM9ahx09J8i30PMIwFgI3' # Pymug - Public API Key
UPLOAD_URL='http://upload.smugmug.com/photos/xmlrawadd.mg'
USER_AGENT='%s/%s +%s' % ('Pymug', __version__, 'http://www.fort-awesome.net/wiki/Pymug')

##########

import urllib
import urllib2
import urlparse
import hashlib

try: 
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError: 
        import django.utils.simplejson as json

class SmugMugError(Exception):
    """Represents an error returned by SmugMug's server."""
    def __init__(self, code, message):
        super(SmugMugError, self).__init__(message)
        self.code = code
        self.message = message

class SmugMugMethod(object):
    def __init__(self, name, request_handler, prefix=None):
        if prefix:
            self._name = "%s.%s" % (prefix, name)
        else:
            self._name = name
        self._request_handler = request_handler
    def __getattr__(self, name):
        if name not in self.__dict__:
            self.__dict__[name] = SmugMugMethod(name, self._request_handler, self._name)
        return self.__dict__[name]
    def __call__(self, **kwargs):
        return self._request_handler(self._name, kwargs)

class SmugMugClient(object):
    def __init__(self, api_key=API_KEY, use_ssl=True, api_version=API_VERSION):
        self.api_key = api_key
        self.api_version = api_version
        self.session_id = None
        self.smugmug = SmugMugMethod('smugmug', self.request)
        # Build the URL
        if use_ssl:
            protocol = 'https'
            domain   = API_DOMAIN_SSL
        else:
            protocol = 'http'
            domain   = API_DOMAIN
        if api_version == "1.2.0":
            directory = 'hack'
        else:
            directory = 'services/api'
        self.api_url = "%s://%s/%s/json/%s/" % (protocol, domain, directory, api_version)

    
    def request(self, method, kwargs):
        """A managed request to SmugMug.
        Login Requests:
          * APIKey will be added if not present
        Other Requests:
          * SessionID will be added if not present
        """
        params = dict(kwargs)
        login_method = method.startswith('smugmug.login')
        # Pre-processing
        if login_method:
            # Login methods get a default APIKey instead of default session id
            if 'APIKey' not in params and self.api_key is not None:
                params['APIKey'] = self.api_key
        elif 'SessionID' not in params and self.session_id is not None:
                params['SessionID'] = self.session_id
        params['method'] = method
        
        # Make request
        url = "?".join((self.api_url, urllib.urlencode(params)))
        result = self._fetch(url)
        
        # Post-processing
        if login_method:
            try:
                self.session_id = result['Login']['Session']['id']
            except KeyError:
                pass
        return result
    
    def upload(self, filename, **kwargs):
        """Upload filename to SmugMug"""
        data = open(filename, 'rb').read()
        params = {
            'Content-Type'      : 'none',
            'Content-Length'    : len(data),
            'Content-MD5'       : hashlib.md5(data).hexdigest(),
            'X-Smug-SessionID'  : self.session_id,
            'X-Smug-Version'    : self.api_version,
            'X-Smug-ResponseType' : 'JSON',
            'X-Smug-FileName'   : filename
        }
        for key, value in kwargs.items():
            params["X-Smug-" + key] = value
        
        upload_request = urllib2.Request(UPLOAD_URL, data, params)
        return self._fetch(upload_request)
    
    @staticmethod
    def _fetch(request):
        """Fetch URL / request from SmugMug and parse accordingly"""
        if not isinstance(request, urllib2.Request):
            request = urllib2.Request(request)
        request.add_header('User-Agent', USER_AGENT)
        response = urllib2.urlopen(request).read()
        result = json.loads(response)
        if result['stat'] != 'ok':
            raise SmugMugError(result.get('code', ""), result.get('message', ""))
        return result

