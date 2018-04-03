"""
Support for status output of APCUPSd via its Network Information Server (NIS).
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/apcupsd/
copied and modified from the original version to support multiple APC servers 
exampe yaml 

multiapcupsd:
  - name: APC1
    ip_address: 192.168.0.1
    port: 3551
  - name: APC2
    ip_address: 192.168.0.2
    port: 3551

"""
import logging
from datetime import timedelta
from homeassistant.util import Throttle

REQUIREMENTS = ['apcaccess==0.0.13']
_LOGGER = logging.getLogger(__name__)
CONF_TYPE = 'type'
DOMAIN = 'multiapcupsd'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
APC = {}

def setup(hass, config):
    """Use config values to set up a function enabling status retrieval."""
    global APC
    devices = config.get('multiapcupsd', {})
    flag = True
    for x in range(0,len(devices)):
        if devices[x]['name']:
            Name = devices[x]['name']
            if devices[x]['ip_address']:
                ip_address = devices[x]['ip_address']
                if devices[x]['port']:
                    port = devices[x]['port']
                    try:
                        APC[Name] = APCUPSdData(ip_address, port)
                        APC[Name].update()
                    except Exception as E:
                        _LOGGER.error('"Failure while testing APCUPSd status retrieval:{0}'.format(E))
                        flag = False
                else:
                    _LOGGER.error('Port not given in configuration {0}'.format(devices[x]))
            else:
                _LOGGER.error('IP address not given in configuration {0}'.format(devices[x]))
        else:
            _LOGGER.error('Name not given in configuration {0}'.format(devices[x]))

    return flag


class APCUPSdData(object):
    """Stores the data retrieved from APCUPSd.
    For each entity to use, acts as the single point responsible for fetching
    updates from the server.
    """

    def __init__(self, host, port):
        """Initialize the data object."""
        from apcaccess import status
        self._host = host
        self._port = port
        self._status = None
        self._get = status.get
        self._parse = status.parse

    @property
    def status(self):
        """Get latest update if throttle allows. Return status."""
        self.update()
        return self._status

    def _get_status(self):
        """Get the status from APCUPSd and parse it into a dict."""
        return self._parse(self._get(host=self._host, port=self._port))

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        """Fetch the latest status from APCUPSd."""
        self._status = self._get_status()