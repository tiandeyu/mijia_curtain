"""Support for Dooya Curtain."""
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

CONF_MODEL = 'model'
DOOYA_CURTAIN_M1 = "dooya.curtain.m1"
BABAI_CURTAIN_BB82MJ = "babai.curtain.bb82mj"

MIOT_MAPPING = {
    # http://miot-spec.org/miot-spec-v2/instances?status=all
    # https://miot-spec.org/miot-spec-v2/instance?type=
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:babai-bb82mj:1:0000C805
    DOOYA_CURTAIN_M1: {
        "motor_control": {"siid": 2, "piid": 2},
        "current_position": {"siid": 2, "piid": 6},
        "target_position": {"siid": 2, "piid": 7},
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:babai-bb82mj:1:0000C805
    BABAI_CURTAIN_BB82MJ: {
        "motor_control": {"siid": 2, "piid": 1},
        "current_position": {"siid": 2, "piid": 2},
        "target_position": {"siid": 2, "piid": 3},
    },
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Required(CONF_MODEL): cv.string,
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    model = config.get(CONF_MODEL)
    cover = DooyaCurtain(name, host, token, model)
    add_devices_callback([cover])


class DooyaCurtain(CoverEntity):
    def __init__(self, name, host, token, model):
        if model == BABAI_CURTAIN_BB82MJ:
            self._action_pause = 0
            self._action_open = 1
            self._action_close = 2
        else:
            self._action_pause = 1
            self._action_open = 2
            self._action_close = 0
        self._model = model
        self._name = name
        self._current_position = 0
        self._target_position = 0
        self._action = 0
        self.miotDevice = MiotDevice(ip=host, token=token, mapping=MIOT_MAPPING[self._model])
        _LOGGER.info("Init miot device: {}, {}".format(self._name, self.miotDevice))

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
        }
        return data

    def update(self):
        self.update_current_position()
        self.update_target_position()
        self.update_action()
        _LOGGER.debug('update_state {} data: {}'.format(self._name, self.state_attributes))

    def update_current_position(self):
        position = self.get_property('current_position')
        if 95 < position < 100:
            position = 100
        if 0 < position < 5:
            position = 0
        self._current_position = position

    def update_target_position(self):
        self._target_position = self.get_property('target_position')

    def update_action(self):
        self._action = self.get_property('motor_control')

    @property
    def is_opening(self):
        self.update_action()
        return self._action == self._action_open

    @property
    def is_closing(self):
        self.update_action()
        return self._action == self._action_close

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

    def open_cover(self, **kwargs) -> None:
        self.miotDevice.set_property("motor_control", self._action_open)

    def close_cover(self, **kwargs):
        self.miotDevice.set_property("motor_control", self._action_close)

    def toggle(self, **kwargs) -> None:
        if self.is_closed:
            self.open_cover(**kwargs)
        else:
            self.close_cover(**kwargs)

    def stop_cover(self, **kwargs):
        self.miotDevice.set_property("motor_control", self._action_pause)

    def set_cover_position(self, **kwargs):
        self.miotDevice.set_property("target_position", kwargs['position'])

    def get_property(self, property_key):
        properties = [{"did": property_key, **MIOT_MAPPING[self._model][property_key]}]
        value = None
        try:
            results = self.miotDevice.get_properties(properties, property_getter="get_properties", max_properties=15)
            for prop in results:
                if prop["code"] == 0 and prop["did"] == property_key:
                    value = prop["value"]
        except Exception:
            _LOGGER.error("Get property {} exception".format(property_key), exc_info=True)
        _LOGGER.debug("{}, {} is: {}".format(self._name, property_key, value))
        return value
