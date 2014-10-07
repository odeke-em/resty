# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import hmac
import hashlib

pyVersion = sys.hexversion / (1<<24)

if pyVersion >= 3:
    import urllib.request as urlReqModule
    byteFyer = {'encoding':'utf-8'}
else:
    import urllib2 as urlReqModule
    byteFyer = {}

try:
    import requests
except ImportError:
    sys.stderr.write("\033[91mFirst install 'requests'\033[00m\n")
    sys.exit(-1)

byteFy = lambda k: bytes(k, **byteFyer)
isCallable = lambda a: hasattr(a, '__call__')
isCallableAttr = lambda obj, attrStr: isCallable(getattr(obj, attrStr, None))

getDefaultAuthor = lambda: os.environ.get('USER', 'Anonymous')
getDefaultUserName = getDefaultAuthor
docStartRegCompile = re.compile('^documents', re.UNICODE)

def getHMACSignature(key, msg, digestmod=hashlib.sha256):
    return hmac.HMAC(key, msg, digestmod)

def getHMACHexDigest(*args, **kwargs):
    return getHMACSignature(*args, **kwargs).hexdigest()

# Custom Exceptions

class UnReadableStreamException(Exception):
    pass

class UnWriteableStreamException(Exception):
    pass
           
def toBytes(data): 
    if isinstance(data, bytes):
        return data

    elif not isinstance(data, str):
        data = str(data)

    return bytes(data, **byteFyer)
