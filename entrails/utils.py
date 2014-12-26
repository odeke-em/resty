# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import sys
import hmac
import hashlib

def pyVersionTuple():
    version = sys.version_info

    if hasattr(version, 'major'):
        return (version.major, version.minor,)
    if isinstance(version, tuple) and len(version) >= 2:
       return (version[0], version[1],)

    return (sys.hexversion/(1<<24), 0,)

majorVersion, minorVersion = pyVersionTuple()
if majorVersion >= 3:
    import urllib.request as urlReqModule
    byteFyer = {'encoding':'utf-8'}
else:
    import urllib2 as urlReqModule
    byteFyer = {}

try:
    import requests
except ImportError:
    sys.stderr.write("\033[94mPlease install 'requests' first by: \033[47m`pip{i} "
        "or pip{i}.{j} requests`\033[00m\n".format(i=majorVersion, j=minorVersion))
    sys.exit(-1)

byteFy = lambda k: bytes(k, **byteFyer)
isCallable = lambda a: hasattr(a, '__call__')
isCallableAttr = lambda obj, attrStr: isCallable(getattr(obj, attrStr, None))

getDefaultAuthor = lambda: os.environ.get('USER', 'Anonymous')
getDefaultUserName = getDefaultAuthor
docStartRegCompile = re.compile('^documents', re.UNICODE)

nonStartSeqReg = re.compile('^[^_a-zA-Z]', re.UNICODE)
unKnownCharSetReg = re.compile('[^_a-zA-Z0-9]+', re.UNICODE)

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

def prepareLiasonName(strPath):
    strPath = nonStartSeqReg.sub('_', str(strPath))
    strPath = unKnownCharSetReg.sub('_', strPath)

    return strPath
