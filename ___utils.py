# Author: Emmanuel Odeke <odeke@ualberta.ca>

import os
import re

isCallable = lambda a: hasattr(a, '__call__')
isCallableAttr = lambda obj, attrStr: isCallable(getattr(obj, attrStr, None))

getDefaultAuthor = lambda: os.environ.get('USER', 'Anonymous')
getDefaultUserName = getDefaultAuthor
docStartRegCompile = re.compile('^documents', re.UNICODE)

# Custom Exceptions

class UnReadableStreamException(Exception):
    pass

class UnWriteableStreamException(Exception):
    pass

