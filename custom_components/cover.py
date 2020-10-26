"""Support for Duya-Mijia covers."""
from homeassistant.components.cover import (
    DOMAIN,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
    CoverEntity,
    DEVICE_CLASS_CURTAIN,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    SERVICE_TOGGLE,
    SERVICE_TOGGLE_COVER_TILT,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
import voluptuous as vol
import logging
from typing import Optional
from datetime import timedelta
from miio.miot_device import MiotDevice

_LOGGER = logging.getLogger(__name__)
CURTAIN_MODEL_BB82MJ = "babai.curtain.bb82mj"

MIOT_MAPPING = {
    CURTAIN_MODEL_BB82MJ: {
        # http://miot-spec.org/miot-spec-v2/instances?status=all
        # Source https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:babai-bb82mj:1:0000C805
        "motor_control": {"siid": 2, "piid": 1},
        "current_position": {"siid": 2, "piid": 2},
        "target_position": {"siid": 2, "piid": 3},
        "mode": {"siid": 2, "piid": 4},
    },
}

ACTION_PAUSE = 0
ACTION_OPEN = 1
ACTION_CLOSE = 2

MODE_NORMAL = 0
MODE_REVERSAL = 1
MODE_CALIBRATE = 2

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    cover = DuyaMijiaCover(name, host, token)
    add_devices_callback([cover])


class DuyaMijiaCover(CoverEntity):

    def __init__(self, name, host, token):
        self._name = name
        self._current_position = 0
        self._target_position = 0
        self._action = 0
        self._mode = 0
        self.miotDevice = MiotDevice(ip=host, token=token, mapping=MIOT_MAPPING[CURTAIN_MODEL_BB82MJ])
        _LOGGER.info("Init miot device: {}, {}".format(name, self.miotDevice))

    @property
    def supported_features(self):
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION

    @property
    def name(self):
        return self._name

    @property
    def device_class(self) -> Optional[str]:
        return DEVICE_CLASS_CURTAIN

    @property
    def state(self):
        """Return the state of the cover."""
        if self.is_opening:
            return STATE_OPENING
        if self.is_closing:
            return STATE_CLOSING
        closed = self.is_closed
        if closed is None:
            return None
        return STATE_CLOSED if closed else STATE_OPEN

    @property
    def state_attributes(self):
        data = {
            'current_position': self._current_position,
            'target_position': self._target_position,
            'action': self._action,
            'mode': self._mode
        }
        return data

    def update(self):
        self.update_current_position()
        self.update_target_position()
        self.update_action()
        self.update_mode()
        _LOGGER.error('update_state data: {}'.format(self.state_attributes))

    def update_current_position(self):
        self._current_position = self.get_property('current_position')

    def update_target_position(self):
        self._target_position = self.get_property('target_position')

    def update_action(self):
        self._action = self.get_property('motor_control')

    def update_mode(self):
        self._mode = self.get_property('mode')

    @property
    def is_opening(self):
        self.update_action()
        return self._action == ACTION_OPEN

    @property
    def is_closing(self):
        self.update_action()
        return self._action == ACTION_CLOSE

    @property
    def is_closed(self):
        self.update_current_position()
        return self._current_position == 0

    @property
    def is_opened(self):
        self.update_current_position()
        return self._current_position == 100

    @property
    def current_cover_position(self):
        self.update_current_position()
        return self._current_position

    @property
    def get_mode(self):
        self.update_mode()
        return self._mode

    def open_cover(self, **kwargs) -> None:
        self.miotDevice.set_property("motor_control", ACTION_OPEN)

    def close_cover(self, **kwargs):
        self.miotDevice.set_property("motor_control", ACTION_CLOSE)

    def stop_cover(self, **kwargs):
        self.miotDevice.set_property("motor_control", ACTION_PAUSE)

    def set_cover_position(self, **kwargs):
        self.miotDevice.set_property("target_position", kwargs['position'])

    def normal(self, **kwargs):
        self.miotDevice.set_property("mode", MODE_NORMAL)

    def reversal(self, **kwargs):
        self.miotDevice.set_property("mode", MODE_REVERSAL)

    def calibrate(self, **kwargs):
        self.miotDevice.set_property("mode", MODE_CALIBRATE)

    def get_property(self, property_key):
        properties = [{"did": property_key, **MIOT_MAPPING[CURTAIN_MODEL_BB82MJ][property_key]}]
        value = None
        try:
            results = self.miotDevice.get_properties(properties, property_getter="get_properties", max_properties=15)
            for prop in results:
                if prop["code"] == 0 and prop["did"] == property_key:
                    value = prop["value"]
        except Exception:
            _LOGGER.error("Get property {} exception".format(property_key), exc_info=True)
        _LOGGER.debug("{} is: {}".format(property_key, value))
        return value
