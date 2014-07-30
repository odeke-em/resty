#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

# This example steps you through using resty & restAssured to save pickled/serialized
# data as a blob and then later re-using it in after deserialization.
# Sample usage might be in collaborative computing ie publish results from an expensive
# computation on one machine so that other machines can load it as live data.

import io
import time
import pickle
import hashlib

import restDriver

triang = lambda i: (i * (i + 1))//2

def main():
    rD = restDriver.RestDriver('http://127.0.0.1', '8000')
    triangs = [triang(i) for i in range(40)]

    checkSumFunc = getattr(hashlib, rD.getCheckSumAlgoName(), None)
    assert(checkSumFunc)
    
    ioObj = io.BytesIO(pickle.dumps(triangs))
    checkSum = checkSumFunc(ioObj.read()).hexdigest()

    # Rewind
    ioObj.seek(0)

    queryAttrs = dict(checkSum=checkSum, checkSumAlgoName=rD.getCheckSumAlgoName())
    manifest = rD.getCloudFilesManifest(**queryAttrs)
    retr = manifest.get('data', None)

    if manifest['status_code'] == 200 and retr:
        print('Previously stored', retr)
        func = rD.updateStream(ioObj, checkSum=checkSum)
    else:
        print('Freshly uploaded', rD.uploadStream(
            ioObj, author='Emmanuel Odeke',
            metaData='First 40 triangulatr number@:%f'%(time.time())
        ))

    dlStream = rD.downloadBlobToStream('blob')

    # Reverted
    if dlStream:
        reloaded = pickle.loads(dlStream.read())
        print('Reloaded as an object\033[47m {} of len: {}\033[00m'.format(
            reloaded, len(reloaded))
        )
        assert(reloaded == triangs)

    # Clean up after yourself
    print('Now cleaning up',  rD.deleteBlob(checkSum=checkSum))

if __name__ == '__main__':
    main()
