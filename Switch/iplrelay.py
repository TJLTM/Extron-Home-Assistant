"""
switch:
  - platform: iplrelay
    name: 

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