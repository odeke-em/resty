# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import re
import hmac
import hashlib

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
