import base64
import hashlib
import json

from typing import List

import requests
import requests.auth

from .util import log

ROBOT_STATES = {
    1: "Cleaning",
    2: "Paused Cleaning",
    3: "Spot Cleaning",
    4: "Paused Spot Cleaning",
    5: "Return",
    6: "Paused Return",
    7: "Return for Pitstop",
    8: "Paused Return for Pitstop",
    9: "Charging",
    10: "Sleeping",
    11: "Error",
    12: "Pitstop",
    13: "Manual Steering",
    14: "Firmware Upgrade"
}

class CloudRobot:
    
    def __init__(self, cloudclient, id, info=None):
        self.cloudclient = cloudclient
        self.id          = id
        self.info        = info
        
        if info:
            self.name           = info["RobotName"]
            self.is_connected   = info["Connected"]
            self.firmware       = info["FirmwareVersion"]
            self.robot_status   = info["RobotStatus"]
            self.battery_status = info["BatteryStatus"]
            self.local_pw       = info["LocalRobotPassword"]
        else:
            self.name           = None
            self.is_connected   = None
            self.firmware       = None
            self.robot_status   = None
            self.battery_status = None
            self.local_pw       = None
        
    def getstatus(self):
        return ROBOT_STATES[self.robot_status]
    
    def startclean(self):
        raise Exception("Not implemented")
    
    def gohome(self):
        raise Exception("Not implemented")
        
    def getid(self) -> str():
        """Get the robot's id"""
        return self.id
    
    def getname(self) -> str:
        """Get the robot's name"""
        return self.name
    
    ###
    
    def getlocalpw(self):
        return self.local_pw
        
    def getMaps(self):
        r = requests.get(self.cloudclient.apiurl + "/robots/" + self.id + "/interactivemaps", auth=self.cloudclient.httpauth)
        
        return list(map(lambda x: CloudMap(self, x["Id"]), r.json()))

class CloudClient:
    
    def __init__(self, email, password):
        password = CloudClient.chksum(password)
        self.apiurl = "https://mobile.rvccloud.electrolux.com/api/v1"
        self.credentials = {
            "AccountPassword": password,
            "Email": email,
        }
        self.httpauth = requests.auth.HTTPBasicAuth(email, password)
        
    @staticmethod
    def chksum(pw):
        buf = pw + "947X6kdLJyrhlCDzUyzFwT4s4NZL3O8eLs0PE4Hi7hU="
        buf = buf.encode("utf-16")[2:]
        return base64.b64encode(hashlib.sha256(buf).digest()).decode("ascii")
        
    def getRobots(self) -> List[CloudRobot]:
        """Get all robots linked to the cloud account"""
        
        url = self.apiurl + "/accounts/ConnectToAccount"
        log("<", url)
        r = requests.post(url, json=self.credentials)
        try:
            return list(map(lambda r: CloudRobot(self, r["RobotID"], r), r.json()["RobotList"]))
        except:
            log("!", "Cannot login: " + str(r))
            
            for k in r.headers:
                log("i", k + ": " + r.headers[k])
            log("i", r.text)
            
    def getRobot(self, id) -> CloudRobot:
        """Make a CloudRobot instance with a given id. id is not checked."""
        return CloudRobot(self, id)
    
class CloudMap:
    
    def __init__(self, cloudrobot, id):
        
        self.cloudclient = cloudrobot.cloudclient
        self.robot       = cloudrobot
        self.id          = id
        self.info        = None
        self.image       = None
        
    def get(self):
        r = requests.get(self.cloudclient.apiurl + "/robots/" + self.robot.id + "/interactivemaps/" + self.id, auth=self.cloudclient.httpauth)
        
        js = r.json()
        
        self.image = base64.b64decode(js["PngImage"])
        
        del js["PngImage"]
        self.info = js
        
        return self.info

###

class CloudRobotv2:
    
    def __init__(self, cloudclient, id):
        self.cloudclient = cloudclient
        self.id          = id
        self._info       = None
        
        
    def _getinfo(self):
        
        if self._info == None:
            url = self.cloudclient.apiurl + "/Appliances/" + self.id
            log("<", url)
            r = requests.get(url, headers=self.cloudclient.headers)
            r.raise_for_status()
            self._info = r.json()["twin"]
            
            log(">", json.dumps(self._info, indent=2))
            
        return self._info
    
    def _getall(self):
        url = self.cloudclient.apiurl + "/Domains/Appliances/" + self.id
        log("<", url)
        r = requests.get(url, headers=self.cloudclient.headers)
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        url = self.cloudclient.apiurl + "/Domains/Appliances/" + self.id + "/Certificate"
        log("<", url)
        r = requests.get(url, headers=self.cloudclient.headers)
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        url = self.cloudclient.apiurl + "/Hashes/Appliances/" + self.id
        log("<", url)
        r = requests.get(url, headers=self.cloudclient.headers)
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        #url = self.cloudclient.apiurl + "/oaq/appliances/" + self.id
        #log("<", url)
        #r = requests.get(url, headers=self.cloudclient.headers)
        #r.raise_for_status()
        #log(">", json.dumps(r.json(), indent=2))
        
        #url = self.cloudclient.apiurl + "/geo/appliances/" + self.id
        #log("<", url)
        #r = requests.get(url, headers=self.cloudclient.headers)
        #r.raise_for_status()
        #log(">", json.dumps(r.json(), indent=2))
        
        url = self.cloudclient.apiurl + "/robots/" + self.id + "/LifeTime"
        log("<", url)
        r = requests.get(url, headers=self.cloudclient.headers)
        r.raise_for_status()
        log(">", json.dumps(r.json(), indent=2))
        
        
        
    ###
        
    def getstatus(self):
        status = self._getinfo()["properties"]["reported"]["robotStatus"]
        return ROBOT_STATES[status]
    
    def startclean(self):
        self._sendCleanCommand("play")
    
    def gohome(self):
        self._sendCleanCommand("home")
        
    def getid(self) -> str():
        """Get the robot's id"""
        return self.id
    
    def getname(self) -> str:
        """Get the robot's name"""
        return self._getinfo()["properties"]["reported"]["applianceName"]
        
    ###
    
    def _sendCleanCommand(self, command):
        # play|stop|home
        # curl -v https://api.delta.electrolux.com/api/Appliances/900277283814002391100106/Commands -X PUT --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --data "{\"CleaningCommand\":\"home\"}" --http1.1 | jq -C .
        r = requests.put(self.cloudclient.apiurl + "/Appliances/" + self.id + "/Commands", headers=self.cloudclient.headers, json={"CleaningCommand": command})
        r.raise_for_status()

class CloudClientv2:
    
    def __init__(self, username, password):
        
        self.client_id = "Wellbeing"
        self.client_secret = "vIpsOBEenIvjbawqL4HA29"
        
        self.apiurl  = "https://api.delta.electrolux.com/api"
        self.headers = {}
        
        self.getToken()
        self.login(username, password)
        
    def getToken(self):
        #TOKEN=$(curl -v https://api.delta.electrolux.com/api/Clients/Wellbeing -X POST --header "Content-Type: application/json" --data '{"ClientSecret":"vIpsOBEenIvjbawqL4HA29"}' --http1.1 | jq .accessToken -r )
        url = self.apiurl + "/Clients/" + self.client_id
        log("<", url)
        r = requests.post(url, json={"ClientSecret":self.client_secret}, headers=self.headers)
        r.raise_for_status()
        token = r.json()["accessToken"]
        self.headers = {"Authorization": "Bearer " + token}
        
    def login(self, username, password):
        #TOKEN2=$(curl -v https://api.delta.electrolux.com/api/Users/Login -X POST --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN" --data "{\"Username\":\"$MAIL\",\"Password\":\"$PASS\"}" --http1.1 | jq .accessToken -r )
        url = self.apiurl + "/Users/Login"
        log("<", url)
        r = requests.post(url, json={"Username":username, "Password": password}, headers=self.headers)
        r.raise_for_status()
        
        token = r.json()["accessToken"]
        self.headers = {"Authorization": "Bearer " + token}
        
    def getRobot(self, id):
        for r in self.getRobots():
            if r.getid() == id:
                return r
        
    def getRobots(self):
        #curl -v https://api.delta.electrolux.com/api/Domains/Appliances -X GET --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --http1.1 | jq -C
        robots = []
        
        r = requests.get(self.apiurl + "/Domains/Appliances", headers=self.headers)
        r.raise_for_status()
        
        appliances = r.json()
        for appliance in appliances:
            #curl -v https://api.delta.electrolux.com/api/Appliances/900277283814002391100106 -X GET --header "Content-Type: application/json" --header "Authorization: Bearer $TOKEN2" --http1.1 | jq -C .
            appliance_id = appliance["pncId"]
            r = requests.get(self.apiurl + "/AppliancesInfo/" + appliance_id, headers=self.headers)
            r.raise_for_status()
            
            if r.json()["device"] == "ROBOTIC_VACUUM_CLEANER":
                robots.append(CloudRobotv2(self, appliance_id))
        
        return robots