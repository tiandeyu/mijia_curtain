"""Support for Mijia Curtain."""
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
    DEVICE_CLASS_GATE,
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
import voluptuous as vol
import logging
import requests
import json
from typing import Optional
from miio.miot_device import MiotDevice

_LOGGER = logging.getLogger(__name__)

ATTR_CURTAIN = 'curtain'
ATTR_AIRER = 'airer'
ATTR_MOTOR_CONTROL = 'motor-control'
ATTR_CURRENT_POSITION = 'current-position'
ATTR_TARGET_POSITION = 'target-position'
ATTR_PAUSE = 'Pause'
ATTR_OPEN = 'Open'
ATTR_UP = 'Up'
ATTR_CLOSE = 'Close'
ATTR_DOWN = 'Down'

CONF_MODEL = 'model'
DOOYA_CURTAIN_M1 = "dooya.curtain.m1"
DOOYA_CURTAIN_M2 = "dooya.curtain.m2"
BABAI_CURTAIN_BB82MJ = "babai.curtain.bb82mj"
LUMI_CURTAIN_HAGL05 = "lumi.curtain.hagl05"
SYNIOT_CURTAIN_SYC1 = "syniot.curtain.syc1"

LUMI_AIRER_ACN01 = "lumi.airer.acn01"


MIOT_MAPPING = {
    # http://miot-spec.org/miot-spec-v2/instances?status=all
    # https://miot-spec.org/miot-spec-v2/instance?type=
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:babai-bb82mj:1:0000C805
    DOOYA_CURTAIN_M1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
    },
    DOOYA_CURTAIN_M2: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:babai-bb82mj:1:0000C805
    BABAI_CURTAIN_BB82MJ: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 3},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 1,
        ATTR_CLOSE: 2,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:lumi-hagl05:1
    LUMI_CURTAIN_HAGL05: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 3},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 1,
        ATTR_CLOSE: 2,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:syniot-syc1:1
    SYNIOT_CURTAIN_SYC1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 2},
        ATTR_PAUSE: 2,
        ATTR_OPEN: 0,
        ATTR_CLOSE: 1,
    },

    LUMI_AIRER_ACN01: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 2},
        ATTR_PAUSE: 2,
        ATTR_OPEN: 0,
        ATTR_CLOSE: 1,
    },
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_MODEL): cv.string,
})


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    model = config.get(CONF_MODEL)
    cover = MijiaCurtain(name, host, token, model)
    add_devices_callback([cover])


def send_http_req(url):
    r = requests.get(url)
    status_code = r.status_code
    if status_code != 200:
        raise RuntimeError('Failing requesting {}'.format(url))
    return json.loads(r.content)


def get_mapping(model, mapping):
    # populate curtain mapping from miot spec rest service
    instance_url = "https://miot-spec.org/miot-spec-v2/instances?status=all"
    instances = send_http_req(instance_url)['instances']
    # get instance by model
    model_instances = [instance for instance in instances if instance['model'] == model]
    if len(model_instances) == 0:
        raise RuntimeError('Failing find model: {} from internet'.format(model))
    services_url = "https://miot-spec.org/miot-spec-v2/instance?type={}".format(model_instances[0]['type'])
    # get service by model
    services = send_http_req(services_url)['services']
    # find curtain properties
    curtain_services = [service for service in services if ATTR_CURTAIN in service['type'] or ATTR_AIRER in service['type']]
    if len(curtain_services) == 0:
        raise RuntimeError('Current device is not a curtain: {}'.format(model))
    curtain_service = curtain_services[0]
    siid = curtain_service['iid']
    curtain_properties = curtain_service['properties']

    motor_control_prop = [prop for prop in curtain_properties if ATTR_MOTOR_CONTROL in prop['type']][0]
    mapping[ATTR_MOTOR_CONTROL]['siid'] = siid
    mapping[ATTR_MOTOR_CONTROL]['piid'] = motor_control_prop['iid']
    value_list = motor_control_prop['value-list']
    mapping[ATTR_PAUSE] = [value for value in value_list if value['description'] == ATTR_PAUSE][0]['value']
    mapping[ATTR_OPEN] = [value for value in value_list if value['description'] in [ATTR_OPEN, ATTR_UP]][0]['value']
    mapping[ATTR_CLOSE] = [value for value in value_list if value['description'] in [ATTR_CLOSE, ATTR_DOWN]][0]['value']

    current_position_prop = [prop for prop in curtain_properties if ATTR_CURRENT_POSITION in prop['type']][0]
    mapping[ATTR_CURRENT_POSITION]['siid'] = siid
    mapping[ATTR_CURRENT_POSITION]['piid'] = current_position_prop['iid']

    target_position_prop = [prop for prop in curtain_properties if ATTR_TARGET_POSITION in prop['type']][0]
    mapping[ATTR_TARGET_POSITION]['siid'] = siid
    mapping[ATTR_TARGET_POSITION]['piid'] = target_position_prop['iid']

    return mapping


class MijiaCurtain(CoverEntity):
    def __init__(self, name, host, token, model):
        self._name = name
        self._current_position = 0
        self._target_position = 0
        self._action = 0
        if model:
            self._model = model
            self._mapping = MIOT_MAPPING[model]
        else:
            self._mapping = {
                ATTR_MOTOR_CONTROL: {"siid": 0, "piid": 0},
                ATTR_CURRENT_POSITION: {"siid": 0, "piid": 0},
                ATTR_TARGET_POSITION: {"siid": 0, "piid": 0},
                ATTR_PAUSE: 0,
                ATTR_OPEN: 0,
                ATTR_CLOSE: 0,
            }
        # init device
        self.miotDevice = MiotDevice(ip=host, token=token, mapping=self._mapping)
        _LOGGER.info("Init miot device: {}, {}".format(self._name, self.miotDevice))
        # if model not config get model from miot device info
        if not model:
            self._model = self.miotDevice.info().model
            self._mapping = get_mapping(self._model, self._mapping)

    @property
    def supported_features(self):
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION

    @property
    def name(self):
        return self._name

    @property
    def device_class(self) -> Optional[str]:
        if ATTR_CURTAIN in self._model:
            return DEVICE_CLASS_GATE
        if ATTR_AIRER in self._model:
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
            ATTR_CURRENT_POSITION: self._current_position,
            ATTR_TARGET_POSITION: self._target_position,
            CONF_MODEL: self._model
        }
        return data

    def update(self):
        self.update_current_position()
        self.update_target_position()
        self.update_action()
        _LOGGER.debug('update_state {} data: {}'.format(self._name, self.state_attributes))

    def update_current_position(self):
        position = self.get_property(ATTR_CURRENT_POSITION)
        if position is None:
            return
        if position:
            if 95 < position < 100:
                position = 100
            if 0 < position < 5:
                position = 0
            self._current_position = position

    def update_target_position(self):
        self._target_position = self.get_property(ATTR_TARGET_POSITION)

    def update_action(self):
        self._action = self.get_property(ATTR_MOTOR_CONTROL)

    @property
    def is_opening(self):
        self.update_action()
        return self._action == self._mapping[ATTR_OPEN]

    @property
    def is_closing(self):
        self.update_action()
        return self._action == self._mapping[ATTR_CLOSE]

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
        self.miotDevice.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_OPEN])

    def close_cover(self, **kwargs):
        self.miotDevice.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_CLOSE])

    def toggle(self, **kwargs) -> None:
        if self.is_closed:
            self.open_cover(**kwargs)
        else:
            self.close_cover(**kwargs)

    def stop_cover(self, **kwargs):
        self.miotDevice.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_PAUSE])

    def set_cover_position(self, **kwargs):
        self.miotDevice.set_property(ATTR_TARGET_POSITION, kwargs['position'])

    def get_property(self, property_key):
        properties = [{"did": property_key, **self._mapping[property_key]}]
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
