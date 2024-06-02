"""Support for Mijia Curtain."""
from homeassistant.components.cover import (
    DOMAIN,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    CoverEntityFeature,
    CoverEntity,
    CoverDeviceClass,
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
import functools as ft
from typing import Optional, Any, final
from miio.miot_device import MiotDevice

_LOGGER = logging.getLogger(__name__)

ATTR_CURTAIN = 'curtain'
ATTR_AIRER = 'airer'
ATTR_LUMI = 'lumi'

ATTR_MOTOR_CONTROL = 'motor-control'
ATTR_STATUS = 'status'
ATTR_CURRENT_POSITION = 'current-position'
ATTR_TARGET_POSITION = 'target-position'

ATTR_PAUSE = 'Pause'
ATTR_OPEN = 'Open'
ATTR_UP = 'Up'
ATTR_CLOSE = 'Close'
ATTR_DOWN = 'Down'
ATTR_STEPPING_UP = 'Stepping Up'
ATTR_STEPPING_DOWN = 'Stepping Down'

ATTR_STOPPED = 'Stopped'
ATTR_OPENING = 'Opening'
ATTR_CLOSING = 'Closing'

CONF_MODEL = 'model'
DOOYA_CURTAIN_M1 = "dooya.curtain.m1"
DOOYA_CURTAIN_M2 = "dooya.curtain.m2"
DOOYA_CURTAIN_C1 = "dooya.curtain.c1"
NOVO_CURTAIN_N21 = "novo.curtain.n21"
BABAI_CURTAIN_BB82MJ = "babai.curtain.bb82mj"
LESHI_CURTAIN_V0001 = "leshi.curtain.v0001"
LUMI_CURTAIN_HAGL05 = "lumi.curtain.hagl05"
LUMI_CURTAIN_HMCN01 = "lumi.curtain.hmcn01"
SYNIOT_CURTAIN_SYC1 = "syniot.curtain.syc1"
PTX_CURTAIN_SIDT82 = "ptx.curtain.sidt82"


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
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:dooya-c1:1
    DOOYA_CURTAIN_C1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_STEPPING_UP: 3,
        ATTR_STEPPING_DOWN: 4,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:novo-n21:1
    NOVO_CURTAIN_N21: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 1,
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
    LESHI_CURTAIN_V0001: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 5},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 6},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:lumi-hagl05:1
    LUMI_CURTAIN_HAGL05: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_STATUS: {"siid": 2, "piid": 6},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 3},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 1,
        ATTR_CLOSE: 2,
        ATTR_STOPPED: 0,
        ATTR_OPENING: 1,
        ATTR_CLOSING: 2,
    },
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:lumi-hmcn01:1
    LUMI_CURTAIN_HMCN01: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_STATUS: {"siid": 2, "piid": 6},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 3},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 1,
        ATTR_CLOSE: 2,
        ATTR_STOPPED: 0,
        ATTR_OPENING: 1,
        ATTR_CLOSING: 2,
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
    # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:curtain:0000A00C:090615-sidt82:1
    PTX_CURTAIN_SIDT82: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 2},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
    }
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


def get_service(model, services):
    # get curtain of airer from model
    device_type = model.split('.')[1]
    name = 'service:{}:'.format(device_type)
    curtain_services = [service for service in services if name in service['type']]
    if len(curtain_services) == 0:
        raise RuntimeError('Current device is not a curtain: {}'.format(model))
    return curtain_services[0]


def get_property(properties, name):
    name = 'property:{}:'.format(name)
    return [prop for prop in properties if name in prop['type']][0]


def get_value(value_list, name_list):
    return [value for value in value_list if value['description'] in name_list][0]['value']


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

    curtain_service = get_service(model, services)
    siid = curtain_service['iid']
    curtain_properties = curtain_service['properties']

    motor_control_prop = get_property(curtain_properties, ATTR_MOTOR_CONTROL)
    mapping[ATTR_MOTOR_CONTROL]['siid'] = siid
    mapping[ATTR_MOTOR_CONTROL]['piid'] = motor_control_prop['iid']
    value_list = motor_control_prop['value-list']
    mapping[ATTR_PAUSE] = get_value(value_list, [ATTR_PAUSE])
    mapping[ATTR_OPEN] = get_value(value_list, [ATTR_OPEN, ATTR_UP])
    mapping[ATTR_CLOSE] = get_value(value_list, [ATTR_CLOSE, ATTR_DOWN])

    # if lumi device get status
    if ATTR_LUMI in model:
        status_prop = get_property(curtain_properties, ATTR_STATUS)
        mapping[ATTR_STATUS]['siid'] = siid
        mapping[ATTR_STATUS]['piid'] = status_prop['iid']
        status_value_list = status_prop['value-list']
        mapping[ATTR_STOPPED] = get_value(status_value_list, [ATTR_STOPPED])
        mapping[ATTR_OPEN] = get_value(status_value_list, [ATTR_OPEN])
        mapping[ATTR_CLOSE] = get_value(status_value_list, [ATTR_CLOSE])

    current_position_prop = [prop for prop in curtain_properties if ATTR_CURRENT_POSITION in prop['type']][0]
    mapping[ATTR_CURRENT_POSITION]['siid'] = siid
    mapping[ATTR_CURRENT_POSITION]['piid'] = current_position_prop['iid']

    target_position_prop = [prop for prop in curtain_properties if ATTR_TARGET_POSITION in prop['type']][0]
    mapping[ATTR_TARGET_POSITION]['siid'] = siid
    mapping[ATTR_TARGET_POSITION]['piid'] = target_position_prop['iid']

    return mapping


class MijiaCurtain(CoverEntity):
    def __init__(self, name, host, token, model):
        self._unique_id = name
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
    def unique_id(self):
        return self._unique_id
    
    @property
    def name(self):
        return self._name

    @property
    def current_cover_position(self):
        return self._current_position
    
    @property
    def current_cover_tilt_position(self):
        if self._current_position > 5:
            return 0
        else:
            return self._current_position * 20

    @property
    def device_class(self) -> Optional[str]:
        if self._model == DOOYA_CURTAIN_C1:
            return CoverDeviceClass.BLIND
        else:
            return CoverDeviceClass.CURTAIN

    @property
    @final
    def state(self):
        if self.is_opening:
            return STATE_OPENING
        if self.is_closing:
            return STATE_CLOSING
        closed = self.is_closed
        if closed is None:
            return None
        return STATE_CLOSED if closed else STATE_OPEN

    @final
    @property
    def state_attributes(self) -> dict[str, Any]:
        data = {
            CONF_MODEL: self._model,
            'current_position': self._current_position,
            'target_position': self._target_position,
        }
        if self._model == DOOYA_CURTAIN_C1:
            data['current_tilt_position'] = self.current_cover_tilt_position
        return data

    @property
    def supported_features(self):
        curtain_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
        blind_features = curtain_features | CoverEntityFeature.OPEN_TILT | CoverEntityFeature.CLOSE_TILT | CoverEntityFeature.SET_TILT_POSITION
        if self._model == DOOYA_CURTAIN_C1:
            return blind_features
        else:
            return curtain_features

    @property
    def is_opening(self):
        if ATTR_LUMI in self._model:
            return self._action == self._mapping[ATTR_OPENING]
        else:
            return self._action == self._mapping[ATTR_OPEN]

    @property
    def is_closing(self):
        if ATTR_LUMI in self._model:
            return self._action == self._mapping[ATTR_CLOSING]
        else:
            return self._action == self._mapping[ATTR_CLOSE]

    @property
    def is_closed(self):
        return self._current_position == 0
    
    @property
    def is_opened(self):
        return self._current_position == 100

    def update(self):
        self.update_current_position()
        self.update_target_position()
        self.update_action()
        _LOGGER.debug('update_state {} data: {}'.format(self._name, self.state_attributes))

    def update_current_position(self):
        position = self.get_property(ATTR_CURRENT_POSITION)
        if self._model != DOOYA_CURTAIN_C1:
            if position is None:
                return
            if 0 < position < 5:
                position = 0
            if 95 < position < 100:
                position = 100
        self._current_position = position

    def update_target_position(self):
        self._target_position = self.get_property(ATTR_TARGET_POSITION)

    def update_action(self):
        if ATTR_LUMI in self._model:
            self._action = self.get_property(ATTR_STATUS)
        else:
            self._action = self.get_property(ATTR_MOTOR_CONTROL)

    def open_cover(self, **kwargs) -> None:
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_OPEN])

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.async_add_executor_job(ft.partial(self.open_cover, **kwargs))

    def close_cover(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_CLOSE])

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self.hass.async_add_executor_job(ft.partial(self.close_cover, **kwargs))

    def toggle(self, **kwargs) -> None:
        if self.is_closed:
            self.open_cover(**kwargs)
        else:
            self.close_cover(**kwargs)

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        fns = {
            "open": self.async_open_cover,
            "close": self.async_close_cover,
            "stop": self.async_stop_cover,
        }
        function = self._get_toggle_function(fns)
        await function(**kwargs)

    def set_cover_position(self, **kwargs):
        self.set_property(ATTR_TARGET_POSITION, kwargs['position'])

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        await self.hass.async_add_executor_job(
            ft.partial(self.set_cover_position, **kwargs)
        )

    def stop_cover(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_PAUSE])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.async_add_executor_job(ft.partial(self.stop_cover, **kwargs))

    def open_cover_tilt(self, **kwargs) -> None:
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_STEPPING_UP])

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        await self.hass.async_add_executor_job(
            ft.partial(self.open_cover_tilt, **kwargs)
        )

    def close_cover_tilt(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_STEPPING_DOWN])

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        await self.hass.async_add_executor_job(
            ft.partial(self.close_cover_tilt, **kwargs)
        )

    def set_cover_tilt_position(self, **kwargs):
        tilt = kwargs['tilt_position']
        position = int((100 - tilt) / 20)
        _LOGGER.debug('Convert tilt to position, tilt: {}, position: {}'.format(tilt, position))
        self.set_property(ATTR_TARGET_POSITION, position)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        await self.hass.async_add_executor_job(
            ft.partial(self.set_cover_tilt_position, **kwargs)
        )

    def stop_cover_tilt(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_PAUSE])

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.async_add_executor_job(
            ft.partial(self.stop_cover_tilt, **kwargs)
        )

    def set_property(self, property_key, value):
        siid = self._mapping[property_key]['siid']
        piid = self._mapping[property_key]['piid']
        self.miotDevice.set_property_by(siid, piid, value)

    def get_property(self, property_key):
        value = None
        try:
            siid = self._mapping[property_key]['siid']
            piid = self._mapping[property_key]['piid']
            results = self.miotDevice.get_property_by(siid, piid)
            for result in results:
                if result["code"] == 0 and result["siid"] == siid and  result['piid'] == piid:
                    value = result["value"]
        except Exception:
            _LOGGER.error("Get property {} exception".format(property_key), exc_info=True)
        _LOGGER.debug("{}, {} is: {}".format(self._name, property_key, value))
        return value

