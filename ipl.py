import logging,socket,re,time
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.const import CONF_PORT, CONF_RESOURCE, CONF_IP_ADDRESS,CONF_NAME,CONF_DEVICE

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ipl'
ComsDict = {}

def setup(hass, config):
    """Set up the IPL component."""
    devices = config.get('ipl', {})
    global ComsDict
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
                            ComsDict[Name] = IPLCommunication(ip_address,port,str(resource))
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
    def __init__(self,IP,Port,ControllerType):
        self.IP = IP
        self.Port = Port
        self.Status = {}
        self.stateTranslation = {'1':True,'0':False}
        self.ConType = ControllerType
        self.Controllers = { 
                        '250':
                            {   
                                'DIO':{     'Ports':[1,2,3,4],
                                            'Serach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4],
                                            'Serach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':[1,2,3,4],
                                            'Query':None}
                            },

                        'CR48':
                            {       
                                'DIO':{     'Ports':[1,2,3,4],
                                            'Serach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4,5,6,7,8],
                                            'Serach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':None,
                                            'Query':None}
                            },

                        'MLC226':
                            {       
                                'DIO':{     'Ports':[1],
                                            'Serach':re.compile(b'Cpn(\d{1}) Sio(0|1)'),
                                            'Query':'{0}O'},
                                'Relay':{   'Ports':[1,2,3,4,5,6],
                                            'Serach':re.compile(b'Cpn(\d{1}) Rly(0|1)'),
                                            'Query':'{0}]'},
                                'IR':   {   'Ports':[1,2],
                                            'Query':None}
                            },
        }
        

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
                        Match = re.match(self.Controllers[self.ConType][item]['Serach'],res[stuff])
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