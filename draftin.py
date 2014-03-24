"""draftin.com API

draftin.com is a markdown based document manager, this module
interacts with its REST API.

Simple usage:
    
    import draftin
    api = draftin.DraftApi('username', 'password')
    doc = api.document(144732)

"""

from __future__ import print_function, unicode_literals, with_statement
import requests
import json
from dateutil.parser import parse as dateparse

try:
    # Python2
    from urlparse import urljoin
except ImportError:
    # Python3
    from urllib.parse import urljoin

DRAFT_API_URL = 'https://draftin.com/api/v1/'

class DraftApiException(Exception):
    """
    Base exception class

    * resp holds the python-requests response object
    * code holds the HTTP response code
    """
    def __init__(self, resp):
        self.response = resp
        self.code = resp.status_code
        if resp.headers.get('Content-Type', '').startswith('application/json'):
            try:
                msg = resp.json().get('error', \
                        'Unknown error invoking the Draft API')
            except:
                msg = resp.text
        else:
            msg = 'Unknown error invoking the Draft API (%d)' % resp.status_code
        Exception.__init__(self, msg)

class DraftApi:
    """Draft API"""

    def __init__(self, user, password):
        """Draft API access object

        Args:
            user(str): account email
            password(str): account password
        """
        self._url = DRAFT_API_URL
        self._user = user
        self._password = password

    @staticmethod
    def _check_response(resp):
        """Raises exception if the response is an error"""
        if resp.status_code < 200 or resp.status_code > 299 :
            raise DraftApiException(resp)

    def request(self, typ, path, **kw):
        """
        Make HTTP request
        - Put Content-type: application/json in POST/PUT
        - Add authentication headers
        - Check response and convert JSON into python struct
        """
        typ = typ.lower()
        url = urljoin(self._url, path)
        fun = getattr(requests, typ)
        if typ == 'post' or typ == 'put':
            headers = {'Content-Type': 'application/json'}
            resp = fun(url, \
                    auth=(self._user, self._password), \
                    headers=headers, **kw)
        else:
            resp = fun(url, auth=(self._user, self._password), **kw)
        self._check_response(resp)

        if resp.status_code == 204 or not resp.headers.get('Content-Type', '').startswith('application/json'):
            return None
        # It seems draft likes to return a string w/ a space when there
        # is nothing to say ... FIXME
        if resp.text == ' ':
            return None
        return resp.json()

    def documents(self):
        """Get list of documents

        returns [DraftDocument] list
        """
        return [ DraftDocument(self, data) for data in self.request('get', 'documents.json')]

    def document(self, docid):
        """Get document with given id

        returns DraftDocument object
        """
        return DraftDocument.from_id(self, docid)

    def create(self, content, name=None):
        """Create a new document

        returns DraftDocument object
        """
        doc = DraftDocument(self)
        doc.update(content, name)
        return doc

    # TODO: FORKS
    # TODO: PEOPLE

class BaseDraftObj:
    """
    Draft Objects inherit from this class
    """

    def __init__(self, api, data=None):
        self.api = api
        self._data = data

    def __getattr__(self, name):
        """
        Get attributes from the internal obj _data
        """
        if self._data and name in self._data:
            return self._data[name]
        raise AttributeError

    def objid(self):
        """returns the object id or None if the object is not saved yet
        
        This should return the same as obj.id, unless the object is empty
        in which case we return None
        """
        return getattr(self, 'id', None)

    def __repr__(self):
        return '%s/%s' % (self.__class__, self.objid())

    def set_data(self, data):
        """Set the data dict"""
        self._data = data

    def updated(self):
        """Return last update date"""
        date = getattr(self, 'created_at', None)
        if date:
            return dateparse(date)
        else:
            return None

    def created(self):
        """Return creation date"""
        date = getattr(self, 'updated_at', None)
        if date:
            return dateparse(date)
        else:
            return None

class DraftSavePoint(BaseDraftObj):
    """A document savepoint in Draft"""
    def __init__(self, api, data):
        BaseDraftObj.__init__(self, api, data)

    def delete(self):
        """Delete savepoint"""
        return self.api.request('delete', 'savepoints/%s.json' %self.objid())

    @staticmethod
    def from_id(api, saveid):
        """Return new SavePoint object for the given id"""
        data = api.request('get', 'savepoints/%s.json' %saveid)
        return DraftSavePoint(api, data)

class DraftDocument(BaseDraftObj):
    """A document stored in Draft"""

    @staticmethod
    def from_id(api, docid):
        """
        Get document with given id
        returns new DraftDocument() object
        """
        data = DraftDocument._get_document(api, docid)
        return DraftDocument(api, data)

    @staticmethod
    def _get_document(api, docid):
        """
        Get document data
        """
        return api.request('get', '/documents/%s.json' % docid)

    def refresh(self):
        """
        Refresh document from remote service
        """
        if not self.objid():
            return
        self.set_data(self._get_document(self.api, self.id))

    def _createdoc(self, content, name=None):
        """
        Create a new document in Draft
        """
        args = {'content' : content}
        if name:
            args['name'] = name
        self.set_data(self.api.request('post', 'documents.json', data=json.dumps(args)))

    def update(self, content, name=None):
        """
        Updates the document content and [name]
        """
        if not self.objid():
            self._createdoc(content, name)
            return

        args = {'content':content}
        if name:
            args['name'] = name
        self.api.request('put', \
                'documents/%s.json' % self.id, data=json.dumps(args))
        self.refresh()

    def delete(self):
        """Delete document

        Upon calling this method this object will be useless
        """
        if not self.objid():
            return
        self.api.request('delete', 'documents/%s.json' % self.id)
        # FIXME: clear dict?

    def savepoints(self):
        """Get all savepoints

        returns [DraftSavePoint] list
        """
        if not self.objid():
            return []
        return [DraftSavePoint(self.api, data) \
                for data in self.api.request('get', 'documents/%s/savepoints.json' % self.id)]

    def createsave(self):
        """Create a new savepoint

        returns DraftSavePoint object or None if this document is empty
        """
        if not self.objid():
            return None
        return self.api.request('POST', \
                        'documents/%s/savepoints.json' % self.id)

    # TODO
    #def compare(self, docid, fork_id):
    #    pass
    #def merge(self, docid, merge):
    #    pass
    #def share(self, docid):
    #    pass

