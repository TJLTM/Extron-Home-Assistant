"""
This provides a central point of communication with an Extron IPL controller
and storage for all the states for that device. I am not using voluptuous 
as it's been a big pain in the ass to use. I will probably add it later.

To use this component: 
1. create a custom_component folder in your homeassistant configuration directory
2. place ipl.py into custom_component/
3. create a yaml entry as per below 

example for a single IPL 250 controller
ipl: 
  - name: Testipl
    resource: 250
    ip_address: 192.168.250.254
    port: 23 

if you have multiple ipls
ipl: 
  - name: Testipl
    resource: 250
    ip_address: 192.168.250.254
    port: 23 
  - name: otherIPL
    resource: CR48
    ip_address: 192.168.250.253
    port: 23  


4. Once this component is setup then use one of the other Components
5. create the appropriate folder and place the component py file there. 
"""

import logging,socket,re,time
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.const import CONF_PORT, CONF_RESOURCE, CONF_IP_ADDRESS,CONF_NAME,CONF_DEVICE

InfoForTheControllers = { 
                        '250':
                            {   
                                'DIO':{     'Ports':[1,2,3,4],
                                            'Searach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4],
                                            'Searach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':[1,2,3,4],
                                            'Query':None}
                            },

                        'CR48':
                            {       
                                'DIO':{     'Ports':[1,2,3,4],
                                            'Searach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4,5,6,7,8],
                                            'Searach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':None,
                                            'Query':None}
                            },

                        'MLC226':
                            {       
                                'DIO':{     'Ports':[1],
                                            'Searach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4,5,6],
                                            'Searach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':[1,2],
                                            'Query':None}
                            },
        }



REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ipl'
ComsDict = {}

def setup(hass, config):
    """Set up the IPL component."""
    devices = config.get('ipl', {})
    global ComsDict,InfoForTheControllers
    flag = True
    for x in range(0,len(devices)):
        if devices[x]['name']:
            Name = devices[x]['name']
            if devices[x]['ip_address']:
                ip_address = devices[x]['ip_address']
                if devices[x]['resource']:
                    resource = devices[x]['resource']
                    if devices[x]['port']:
                        port = devices[x]['port']
                        try:
                            ComsDict[Name] = IPLCommunication(ip_address,port,str(resource),InfoForTheControllers)
                        except Exception as E:
                            _LOGGER.error('Can not create Communication channel for IPL Box:{0}'.format(E))
                            flag = False
                    else:
                        _LOGGER.error('Port not given in configuration {0}'.format(devices[x]))
                else:
                    _LOGGER.error('Resource not given in configuration {0}'.format(devices[x]))
            else:
                _LOGGER.error('IP address not given in configuration {0}'.format(devices[x]))
        else:
            _LOGGER.error('Name not given in configuration {0}'.format(devices[x]))

    return flag

class IPLCommunication():
    def __init__(self,IP,Port,ControllerType,info):
        """ Communication with the IPL Controller is done through this class
        The TCP connection to the Device is only open when a query is being 
        made or a command is being sent. 
        """
        self.IP = IP
        self.Port = Port
        self.Status = {}
        self.stateTranslation = {'1':True,'0':False}
        self.ConType = ControllerType
        self.Controllers = info
        self.Status = {}
        for key in self.Controllers[self.ConType]:
            portdict = {}
            if self.Controllers[self.ConType][key]['Query'] != None:
                for num in self.Controllers[self.ConType][key]['Ports']:
                    portdict[num] = False

                self.Status[key] = portdict

    def Update(self,Num):
        if Num == 1:
            sleepTime = .1
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.IP,self.Port))
            time.sleep(sleepTime)
            sock.send(b'w3cv\r')
            for key in self.Status:
                for x in self.Status[key]:
                    if self.Controllers[self.ConType][key]['Query'] != None:
                        CmdString = self.Controllers[self.ConType][key]['Query'].format(x)
                        sock.send(CmdString.encode())
                
            time.sleep(1)
            res = sock.recv(2048).split(b'\r\n')
            for stuff in range(4,len(res)-1):
                for item in self.Status:
                    if item in ['Relay','DIO']:
                        Match = re.match(self.Controllers[self.ConType][item]['Searach'],res[stuff])
                        if Match: 
                            self.Status[item][int(Match.group(1).decode())] = self.stateTranslation[Match.group(2).decode()]

            sock.close()

    def IRCommand(self,Number):
        pass

    def SetDIOOutput(self,Num,State):
        pass

    def GetSourceInputMLC226(self):
        pass

    def GetInput(self,Number):
        return self.Status['DIO'][Number]

    def GetRelay(self,Number):
        return self.Status['Relay'][Number]

    def SetRelay(self,Number,State):  
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.IP,self.Port))
        time.sleep(.1)
        CmdString = '{0}*{1}O'.format(Number,State)
        sock.send(CmdString.encode())
        self.Status['Relay'][Number] = self.stateTranslation[State]
        time.sleep(.1)
        sock.close()