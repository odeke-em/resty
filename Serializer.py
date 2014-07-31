#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import io
import json
import pickle
import hashlib

isCallable = lambda a: a and hasattr(a, '__call__')

class Serializer:
    def __init__(self, serialzr=None, deserialzr=None, preSerializr=None):
        self.__serializer = serialzr
        self.__deserializer = deserialzr

    def serialize(self, data):
        if isCallable(self.__serializer):
            return self.__serializer(data)

    def deserialize(self, data):
        if isCallable(self.__deserializer):
            return self.__deserializer(data)

    def ___convo(self, data, expected, aux=None):
        if isinstance(data, expected) or not isinstance(data, aux):
            return data

        print('d', data, 'e', expected)
        return expected(data, encoding='utf-8')

    def byteFy(self, data):
        return self.___convo(data, bytes, str)

    def stringify(self, data):
        return self.___convo(data, str, bytes)

    def ioStream(self, data):
        return data

class BinarySerializer(Serializer):
    def __init__(self):
        super(BinarySerializer, self).__init__(serialzr=pickle.dumps, deserialzr=pickle.loads)

    def ioStream(self, data):
        return io.BytesIO(super().byteFy(self.serialize(data)))

class JSONSerializer(Serializer):
    def __init__(self):
        super(JSONSerializer, self).__init__(serialzr=json.dumps, deserialzr=json.loads)

    def ioStream(self, data):
        return io.StringIO(super().stringify(data))
