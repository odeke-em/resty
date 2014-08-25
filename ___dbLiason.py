#!/usr/bin/python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import sys
import json
import collections

pyVersion = sys.hexversion / (1<<24)

if pyVersion >= 3:
        import urllib.request as urlReqModule
        byteFyer = {'encoding':'utf-8'}
else:
        import urllib2 as urlReqModule
        byteFyer = {}

class DbConn:
    _rawUrlRequester = urlReqModule

    def __init__(self, baseUrl):
        self.baseUrl = baseUrl

    def __urlRequest(self, method, isGet=False, **getData):
        fmtdData = json.dumps(getData)
        reqUrl = self.baseUrl
        if isGet:
            reqUrl = self.baseUrl + '/?' + '&'.join(
                ['{k}={v}'.format(k=k, v=v) for k,v in getData.items()]
            )

        req = self._rawUrlRequester.Request(reqUrl)
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda : method.upper()

        dataOut = {}
        statusCode = 500
        try:
            uR = self._rawUrlRequester.urlopen(req, bytes(fmtdData, **byteFyer))
        except Exception as e:
            print(e)
            dataOut['reason'] = e
        else:
            # Next attempt to json parse the data
            try:
                jsonParsed = json.loads(uR.read().decode())
            except Exception as e:
                dataOut['reason'] = e
            else:
                dataOut['value'] = jsonParsed
                statusCode = uR.getcode()

        finally:
            dataOut['status_code'] = statusCode

        return dataOut

    def setBaseURL(self, baseURL):
        self.baseUrl = baseURL

    def getBaseURL(self):
        return self.baseUrl

    def get(self, **data):
        return self.__urlRequest('get', isGet=True, **data)

    def put(self, **data):
        return self.__urlRequest('put', **data)

    def post(self, **data):
        return self.__urlRequest('post', **data)

    def delete(self, **data):
        return self.__urlRequest('delete', **data)

class HandlerLiason(object):
    _rawUrlRequester = DbConn._rawUrlRequester
    def __init__(self, baseUrl, *args, **kwargs):
        self.baseUrl = baseUrl
        self.handler = DbConn(baseUrl)

    def postConn(self, **data):
        return self.handler.post(**data)

    def deleteConn(self, **data):
        return self.handler.delete(**data)

    def putConn(self, **data):
        return self.handler.put(**data)

    def getConn(self, **data):
        return self.handler.get(**data)
