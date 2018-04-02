"""
this component pulls the config of this device from the IPL 
component and sets up all the relays on that controller (resource 
in the configuration). 

To use this component: 
1. Setup the ipl component instructions
2. create custom_component/switch and place iplrelay.py into that folder 
3. make note of the Name of the IPL you want to use the relays on,
   from the name used in the ipl component. as that is how this 
   components communicates with that device

4. create a yaml entry as per below 

ipl: 
  - name: deviceName
    ...

Example Yaml configuration 
switch:
  - platform: iplrelay
    name: deviceName

"""
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import CONF_NAME, CONF_TYPE,CONF_FRIENDLY_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.ipl as IPL

DEPENDENCIES = ['ipl']

_LOGGER = logging.getLogger(__name__)

PIN_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

SCAN_INTERVAL = timedelta(seconds=10)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the IPL Relay platform."""
    if IPL.ComsDict == {}:
        _LOGGER.error("A connection has not been made to the IPL")
        return False
    else:
        switches = []
        Name = config.get(CONF_NAME)
        Coms = IPL.ComsDict[Name]
        for x in Coms.Controllers[Coms.ConType]['Relay']['Ports']:
            switches.append(IPLRELAY('{0}:{1}'.format(Name,x),x,Coms))
        add_devices(switches)


class IPLRELAY(SwitchDevice):
    """Representation of a switch that can be toggled using SIS commands."""

    def __init__(self, friendly_name, relay, Coms):
        """Initialize the switch."""
        self._name = friendly_name
        self._relaynum = relay
        self.Coms = Coms

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """Always Poll"""
        return True

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.Coms.GetRelay(self._relaynum)

    def update(self):
        """Update device state."""
        self.Coms.Update(self._relaynum)

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.Coms.SetRelay(self._relaynum,'1')

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.Coms.SetRelay(self._relaynum,'0')