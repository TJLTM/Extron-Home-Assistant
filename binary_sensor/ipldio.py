"""
this component pulls the config of this device from the IPL 
component and sets up all the DIO on that controller (resource 
in the configuration). 

To use this component: 
1. Setup the ipl component instructions
2. create custom_component/binary_sensor and place ipldio.py into that folder 
3. make note of the Name of the IPL you want to use the relays on,
   from the name used in the ipl component. as that is how this 
   components communicates with that device

4. create a yaml entry as per below 

ipl: 
  - name: deviceName
    ...

Example Yaml configuration 
binary_sensor:
  - platform: ipldio
    name: deviceName
"""
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import CONF_NAME, CONF_TYPE,CONF_FRIENDLY_NAME
import homeassistant.helpers.config_validation as cv
import custom_components.ipl as IPL
_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['ipl']

PIN_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
})

SCAN_INTERVAL = timedelta(seconds=10)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the IPL DIO platform."""
    if IPL.ComsDict == {}:
        _LOGGER.error("A connection has not been made to the IPL")
        return False
    else:
        dio = []
        Name = config.get(CONF_NAME)
        Coms = IPL.ComsDict[Name]
        for x in Coms.Controllers[Coms.ConType]['DIO']['Ports']:
            dio.append(IPLDIO('{0}:{1}'.format(Name,x),x,'Digital Input',Coms))

        add_devices(dio)

class IPLDIO(BinarySensorDevice):
    """ IPL binary sensor."""

    def __init__(self, name,DeviceNumber,device_class,Coms):
        """Initialize the sensor."""
        self._name = name
        self._sensor_type = device_class
        self.Coms = Coms
        self.DeviceNumber = DeviceNumber

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._sensor_type

    @property
    def should_poll(self):
        """always poll."""
        return True

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.Coms.GetInput(self.DeviceNumber)

    def update(self):
        """Update device state."""
        self.Coms.Update(self.DeviceNumber)