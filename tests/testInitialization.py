import unittest

import restDriver

class TestInit(unittest.TestCase):
    def testConstructorWithNoArgs(self):
        rd = restDriver.RestDriver(None, None)
        self.assertEqual(rd.getBaseUrl(), 'http://127.0.0.1:8000')

        rd = restDriver.RestDriver('', '')
        self.assertEqual(rd.getBaseUrl(), 'http://127.0.0.1:8000')

    def testConstructorAndCheckSumName(self):
        rd1 = restDriver.RestDriver('', checkSumAlgoName='sha1')
        self.assertEqual(rd1.getCheckSumAlgoName(), 'sha1')
        self.assertEqual(rd1.getBaseUrl(), 'http://127.0.0.1:8000')

        rd2 = restDriver.RestDriver('', checkSumAlgoName='md5')
        self.assertEqual(rd2.getCheckSumAlgoName(), 'md5')
        self.assertEqual(rd2.getBaseUrl(), 'http://127.0.0.1:8000')

    def testSecretKeyInit(self):
        rd1 = restDriver.RestDriver('', secretKey=__file__)

        items = (1234, 'abcdEFGH', b'458485', None, self, '', rd1, restDriver,)
        signedR1 = rd1.signItems(outputPlainBytes=False, *items)
        self.assertEqual(len(signedR1), len(items))
        for sres1 in signedR1:
            # Expecting sre1 to be hexdigest ie str
            self.assertEqual(isinstance(sres1, str), True)

        signedR2 = rd1.signItems(outputPlainBytes=True, *items)
        self.assertEqual(len(signedR2), len(items))
        for sres2 in signedR2:
            # Expecting sre2 to be plain bytes
            self.assertEqual(isinstance(sres2, bytes), True)
