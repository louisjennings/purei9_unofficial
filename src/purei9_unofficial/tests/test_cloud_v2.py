import itertools
import unittest
import time

from .util import load_secrets

from .. import cloud
from .. import common

SECRETS  = load_secrets()
USERNAME = SECRETS["cloud"]["username"]
PASSWORD = SECRETS["cloud"]["password"]
ROBOTID  = SECRETS["local"]["robotid"]
LOCALPW  = SECRETS["local"]["localpassword"]

class TestCloud(unittest.TestCase):

    def test_01(self):
        cc = cloud.CloudClientv2(USERNAME, PASSWORD)
        cc.tryLogin()
        
        ###
        # Token generation
        ###
        
        token = cc.gettoken()
        
        cc2 = cloud.CloudClientv2(token=token)
        cc2.tryLogin()
        
        ###
        # Robot list
        ###
        
        self.assertIn(ROBOTID, map(lambda rc: rc.getid(), cc.getRobots()), "Robot not found in cloud list")
        rc = cc.getRobot(ROBOTID)
        
        ###
        # Basic Stuff
        ###
        
        rc.getid()
        rc.getname()
        rc.getfirmware()
        rc.getbattery()

if __name__ == '__main__':
    unittest.main()
