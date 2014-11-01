import unittest

import restDriver

isCallableAttr = restDriver.isCallableAttr

class TestInit(unittest.TestCase):
    def setUp(self):
        self.rd = restDriver.RestDriver(None, None)
        self.assertEqual(self.rd.getBaseUrl(), 'http://127.0.0.1:8000')

    def testPlainRegistration(self):
        self.rd.registerLiason('song', '/thebear/songHandler')

        self.assertEqual(isCallableAttr(self.rd, 'newSong'), True)
        self.assertEqual(isCallableAttr(self.rd, 'getSongs'), True)
        self.assertEqual(isCallableAttr(self.rd, 'updateSongs'), True)
        self.assertEqual(isCallableAttr(self.rd, 'deleteSongs'), True)

    def testUnknownStartSeqRegistration1(self):
        self.rd.registerLiason('0Auth', '/auth/oauth')
        self.assertEqual(isCallableAttr(self.rd, 'new_auth'), True)
        self.assertEqual(isCallableAttr(self.rd, 'get_auths'), True)
        self.assertEqual(isCallableAttr(self.rd, 'update_auths'), True)
        self.assertEqual(isCallableAttr(self.rd, 'delete_auths'), True)

    def testUnknownStartSeqRegistration2(self):
        self.rd.registerLiason(' device', '/auth/oauth')
        self.assertEqual(isCallableAttr(self.rd, 'new_device'), True)
        self.assertEqual(isCallableAttr(self.rd, 'get_devices'), True)
        self.assertEqual(isCallableAttr(self.rd, 'update_devices'), True)
        self.assertEqual(isCallableAttr(self.rd, 'delete_devices'), True)

    def testUnknownCharSetForRegistration(self):
        self.rd.registerLiason('/auth/app', '/auth/authHandler')
        self.assertEqual(isCallableAttr(self.rd, 'get_auth_apps'), True)
        self.assertEqual(isCallableAttr(self.rd, 'new_auth_app'), True)
        self.assertEqual(isCallableAttr(self.rd, 'update_auth_apps'), True)
        self.assertEqual(isCallableAttr(self.rd, 'delete_auth_apps'), True)

    def testExtremeContentForRegistration(self):
        self.assertEqual(self.rd.registerLiason(self, None), None)
        self.assertEqual(self.rd.registerLiason({}, 'NAN'), None)
        self.assertEqual(self.rd.registerLiason('hey', 1000), None)
        self.assertEqual(self.rd.registerLiason(None, None), None)
        self.assertEqual(self.rd.registerLiason('', '', None), None)
