resty
=====

Client side kit for use with restAssured.

Sample Usage:
============
    * First step is including resty in your project so that your project space looks like this:
        projectSrc/
            resty
            test.py
            ...
    * Next step is using resty in your code.
    * This example assumes that for successful running, you have cloned and are running
        [restAssured](https://github.com/odeke-em/restAssured.git) on the ip and port that you
        will provide when running sampleResty.py
    * Also it runs code from restAssured projects jobTable which saves jobs that are pushed up
      and will later on be assigned to different workers. Also the example shows how to use the
      file handling service with restAssured.
    * vi sampleResty.py

        #!/usr/bin/env python

        import os
        from resty import restDriver

        getDefaultAuthor = lambda: os.environ.get('USERNAME', 'Anonymous')

        def main():
            port = '8000'
            address = 'http://127.0.0.1'

            restDriver = RestDriver(address, port)

            # First step is registering a liason by its referral name eg 'Job',
              and then it's handler uri. 
            # After registration, referring to the CRUD handlers of the liason will be as simple
            # as invoking eg newJob, getJobs, updateJobs, deleteJobs

            restDriver.registerLiason('Job', '/jobTable/jobHandler')
            restDriver.registerLiason('Worker', '/jobTable/workerHandler')

            print(restDriver.newWorker(name='SpeedBuggy', purpose='Individual Checks'))
            print(restDriver.newJob(
                message='TheStrokes-Someday', author=getDefaultAuthor(), assignedWorker_id=1
            ))

            print(restDriver.updateWorkers(
                queryParams=dict(name='SpeedBuggy'), updatesBody=dict(purpose='Crawling Speed checks')
            ))

            print('Updating', restDriver.updateJobs(
                queryParams=dict(message='TheStrokes-Someday'), updatesBody=dict(status='finished')
            ))

            # Handling D for Jobs and Workers
            print(restDriver.deleteJobs())
            print(restDriver.deleteWorkers())

            # Handling G for file handling app
            print(restDriver.getCloudFilesManifest(select='size,checkSum'))

            # Handling D for file handling app
            print(restDriver.deleteBlob(title='collabFib'))

            restDriver.registerLiason('Artist', '/thebear/artistHandler')
            print(restDriver.newArtist(name='Tester'))

        if __name__ == '__main__':
            main()

    + This next example steps you through using resty & restAssured to save pickled/serialized
    + data as a blob and then later re-using it in after deserialization.
        * Sample usage might be in collaborative computing ie publish results from an expensive
        * computation on one machine so that other machines can load it as live data.

        + vi blobStore.py

        #!/usr/bin/env python3

        import io
        import time
        import pickle
        import hashlib

        import restDriver

        triang = lambda i: (i * (i + 1))//2

        def main():
            rDriver = restDriver.RestDriver('http://127.0.0.1', '8000')
            triangs = [triang(i) for i in range(40)]

            checkSumFunc = getattr(hashlib, rDriver.getCheckSumAlgoName(), None)
            assert(checkSumFunc)
    
            ioObj = io.BytesIO(pickle.dumps(triangs))
            checkSum = checkSumFunc(ioObj.read()).hexdigest()

            # Rewind
            ioObj.seek(0)

            queryAttrs = dict(checkSum=checkSum, checkSumAlgoName=rDriver.getCheckSumAlgoName())
            manifest = rDriver.getCloudFilesManifest(**queryAttrs)
            retr = manifest.get('data', None)

            if manifest['status_code'] == 200 and retr:
                print('Previously stored', retr)
                print('Now updating the streams', rDriver.updateStream(ioObj, checkSum=checkSum))
            else:
                print('Freshly uploaded', rDriver.uploadStream(
                    ioObj, author='Emmanuel Odeke',
                    metaData='First 40 triangular numbers@:%f'%(time.time())
                ))

            dlStream = rDriver.downloadBlobToStream('blob')

            # DeSerializing
            if dlStream:
                reloaded = pickle.loads(dlStream.read())
                print('Reloaded as an object\033[47m {} of len: {}\033[00m'.format(
                    reloaded, len(reloaded))
                )
                assert(reloaded == triangs)

            # Clean up after yourself
            print('Now cleaning up',  rDriver.deleteBlob(checkSum=checkSum))

        if __name__ == '__main__':
            main()
