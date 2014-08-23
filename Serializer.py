#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import io
import json
import pickle

try:
    from ___utils import isCallable
except:
    from .___utils import isCallable

class Serializer:
    def __init__(self, serialzr=None, deserialzr=None, preSerializr=None):
        self.__serializer = serialzr
        self.__deserializer = deserialzr

    def serialize(self, data):
        if isCallable(self.__serializer):
            return self.__serializer(data)

    def deserialize(self, data):
        if isCallable(self.__deserializer):
            return self.__deserializer(self.preDeserialization(data))

    def ___convo(self, data, expected, aux=None):
        if isinstance(data, expected):
            return data
        elif isinstance(data, aux):
            return expected(data, encoding='utf-8')
        else:
            return expected(data)

    def byteFy(self, data):
        return self.___convo(data, bytes, str)

    def stringify(self, data):
        return self.___convo(data, str, bytes)

    def ioStream(self, data):
        return data

    def preHasher(self, data):
        return data

    def preDeserialization(self, data):
        return data

class BinarySerializer(Serializer):
    def __init__(self):
        super(BinarySerializer, self).__init__(serialzr=pickle.dumps, deserialzr=pickle.loads)

    def ioStream(self, data):
        return io.BytesIO(super().byteFy(super().serialize(data)))

    def preHasher(self, data):
        return super().byteFy(data)

    def preDeserialization(self, data):
        return super().byteFy(data)

class JSONSerializer(Serializer):
    def __init__(self):
        super(JSONSerializer, self).__init__(serialzr=json.dumps, deserialzr=json.loads)

    def ioStream(self, data):
        return io.StringIO(super().stringify(super().serialize(data)))

    def preHasher(self, data):
        return super().byteFy(data)

    def preDeserialization(self, data):
        return super().stringify(data)
