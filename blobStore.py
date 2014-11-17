#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

# This example steps you through using resty & restAssured to save pickled/serialized
# data as a blob and then later re-using it in after deserialization.
# Sample usage might be in collaborative computing ie publish results from an expensive
# computation on one machine so that other machines can load it as live data.

def testSerializer():
    import Serializer
    bs = Serializer.BinarySerializer()
    js = Serializer.JSONSerializer()
    data = dict((i, i) for i in range(10))
    bserial = bs.serialize(data)
    jserial = js.serialize(data)

    bdserial = bs.deserialize(bserial)
    jdserial = js.deserialize(jserial)
    print('bdserial', bdserial)

    ioS = bs.ioStream(bserial)
    ioR = ioS.read()
    print('ioS data from the stream', ioR)

def testCloudPassagePickledVersion():
    from entrails.cloudPassage import CloudPassageHandler
    cc = CloudPassageHandler()
    data = dict((i, i*10) for i in range(9))
    title = 'Dict of items 0-8999, keys i*10'
    res = cc.push(data, title=title, asPickle=True)
    pulledObj = cc.pull(metaData='pickle')

    print('PulledObj', pulledObj, data)
    assert(pulledObj == data)

    rmTry = cc.removeTrace(data, asPickle=True)
    print(rmTry)

def testCloudPassageJSONVersion():
    from entrails.cloudPassage import CloudPassageHandler
    cc = CloudPassageHandler()
    data = dict((str(i), i*10) for i in range(9))
    title = 'Dict of items 0-8999, keys i*10'
    res = cc.push(data, title=title, asPickle=False)
    pulledObj = cc.pull(metaData='json')

    print('PulledObj', pulledObj, data)
    assert(pulledObj == data)

    rmTry = cc.removeTrace(data)
    print(rmTry)

def main():
    testSerializer()
    testCloudPassageJSONVersion()
    testCloudPassagePickledVersion()

if __name__ == '__main__':
    main()
