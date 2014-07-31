#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import io
import time
import pickle
import hashlib

import restDriver
import Serializer

class CloudPassageHandler:
    def __init__(self, addr='http://127.0.0.1', port='8000'):
        self.__restDriver = restDriver.RestDriver(addr, port)

        self.__checkSumFunc = self.getCheckSumFunc()
        self.__jsonSerializer = Serializer.JSONSerializer()
        self.__pickleSerializer = Serializer.BinarySerializer()

    def getCheckSumFunc(self):
        return getattr(hashlib, self.__restDriver.getCheckSumAlgoName(), None)

    def computeCheckSum(self, data):
        return self.__checkSumFunc(data).hexdigest()

    def __selectSerializer(self, jsonToggle):
        if jsonToggle:
            return self.__jsonSerializer, 'json'

        return self.__pickleSerializer, 'pickle'

    def push(self, rawObject, asPickle=False, **kwargs):
        selector, sType = self.__selectSerializer(asPickle)

        checkSum = self.computeCheckSum(selector.serialize(rawObject))

        # We maintain uniqueness
        status, retr = self.__manifestPull(checkSum=checkSum, metaData=sType, **kwargs)
        stream = selector.ioStream(rawObject)
        kwargs.setdefault('uri', 'Computation@%s'%(time.time()))

        if status == 200 and retr:
            return self.__restDriver.updateStream(stream, checkSum=checkSum, metaData=sType, **kwargs)
        else:
            return self.__restDriver.uploadStream(stream, checkSum=checkSum, metaData=sType, **kwargs)

    def removeTrace(self, rawObj, asPickle=False, **kwargs):
        selector, sType = self.__selectSerializer(asPickle)
        checkSum = self.computeCheckSum(selector.serialize(rawObj))

        return self.__restDriver.deleteBlob(checkSum=checkSum, metaData=sType)

    def pull(self, **queryMap):
        # Returns the deserialized object essentially the 'live object'
        status, data = self.__manifestPull(**queryMap)
        if status == 200:
            keyName = data.get('content', None)
            if keyName:
                stream = self.__restDriver.downloadBlobToStream(keyName)
                if stream and Serializer.isCallable(stream.read):
                    metaType = queryMap.get('metaData', None)

                    selector = None
                    if metaType == 'json': 
                        selector = self.__jsonSerializer
                    elif metaType == 'pickle':
                        selector = self.__pickleSerializer

                    if selector:
                        return selector.deserialize(stream.read())

    def __manifestPull(self, **identifiers):
        # Returns <errCode>, <data>
        manifest = self.__restDriver.getCloudFilesManifest(**identifiers)
        status = manifest.get('status_code', 400)

        if status != 200:
            return status, manifest
        else:
            retr = manifest.get('data', None)
            if retr:
                headItem = retr[0]
                return 200, headItem

            return 404, manifest
