#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import json
import requests
import collections

class DbConn:
    def __init__(self, baseUrl, tokenRetrievalURL=None):
        self.baseUrl = baseUrl
        self.__initSessionStore()
        self.___createHTTPHandlers()

        if tokenRetrievalURL:
            self.refreshTokenStore(tokenRetrievalURL)
    
    def __initSessionStore(self):
        self.__sessionStore = requests.Session()
        self._updateHeaders({'Content-Type': 'application/json'})

    def _updateHeaders(self, headerDict):
        self.__sessionStore.headers.update(headerDict)

    def refreshTokenStore(self, tokenRetrievalUrl):
        rget = self.__sessionStore.get(tokenRetrievalUrl)

    def __createHandler(self, methodName):
        func = getattr(self.__sessionStore, methodName, None)
        assert func != None, 'Expecting a successful op'

        def performer(**data):
            return self.__performOp(func, data=data)

        return performer

    def ___createHTTPHandlers(self):
        _handlers = ('get', 'put', 'delete', 'post',)

        for methodName in _handlers:
            func = self.__createHandler(methodName)
            setattr(self, methodName, func)

    def __performOp(self, func, *args, **kwargs):
        dataOut = {}
        result = func(self.baseUrl, *args, **kwargs)
        statusCode = result.status_code

        try:
            jsonParsed = result.json()
        except ValueError as e: # Could not parse JSON from text
            dataOut['reason'] = result.text
        except Exception as e: # Other exception
            dataOut['reason'] = e
        else:
            dataOut['value'] = jsonParsed
        finally:
            dataOut['status_code'] = statusCode

        return dataOut

    def setBaseURL(self, baseURL):
        self.baseUrl = baseURL

    def getBaseURL(self):
        return self.baseUrl

class HandlerLiason(object):
    def __init__(self, baseUrl, *args, **kwargs):
        self.baseUrl = baseUrl
        self.handler = DbConn(baseUrl, *args, **kwargs)

    def postConn(self, **data):
        return self.handler.post(**data)

    def deleteConn(self, **data):
        return self.handler.delete(**data)

    def putConn(self, **data):
        return self.handler.put(**data)

    def getConn(self, **data):
        return self.handler.get(**data)


def main():
    dc = DbConn('http://127.0.0.1:8000')

    assert dc.get, "Get method must exist"
    assert dc.put, "Put method must exist"
    assert dc.post, "Post method must exist"
    assert dc.delete, "Delete method must exist"

    assert hasattr(dc.get, "__call__"), "Get must be callable"
    assert hasattr(dc.put, "__call__"), "Put must be callable"
    assert hasattr(dc.post, "__call__"), "Post must be callable"
    assert hasattr(dc.delete, "__call__"), "Delete must be callable"

    hl = HandlerLiason('http://127.0.0.1:8000/thebear')

    assert hl.getConn, "Expected the getConn"
    assert hl.putConn, "Expected the putConn"
    assert hl.postConn, "Expected the postConn"
    assert hl.deleteConn, "Expected the deleteConn"

    print(hl.getConn())

if __name__ == '__main__':
    main()
