"""Support for Mijia Curtain."""

import functools as ft
import json
import logging
from typing import Any, Optional, final

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol

from homeassistant.components.cover import (
    DOMAIN,
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
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
from miio import Device as MiioDevice
from miio.miot_device import MiotDevice


_LOGGER = logging.getLogger(__name__)

ATTR_CURTAIN = "curtain"
ATTR_AIRER = "airer"
ATTR_LUMI = "lumi"

ATTR_MOTOR_CONTROL = "motor-control"
ATTR_STATUS = "status"
ATTR_CURRENT_POSITION = "current-position"
ATTR_TARGET_POSITION = "target-position"

ATTR_PAUSE = "Pause"
ATTR_OPEN = "Open"
ATTR_UP = "Up"
ATTR_CLOSE = "Close"
ATTR_DOWN = "Down"
ATTR_STEPPING_UP = "Stepping Up"
ATTR_STEPPING_DOWN = "Stepping Down"

ATTR_STOPPED = "Stopped"
ATTR_OPENING = "Opening"
ATTR_CLOSING = "Closing"

# legacy 协议 get_prop 返回属性顺序配置 key
ATTR_LEGACY_PROPS = "_legacy_props"

CONF_MODEL = "model"

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


DEFAULT_LEGACY_PROPS = [
    ATTR_CURRENT_POSITION,
    ATTR_TARGET_POSITION,
    ATTR_MOTOR_CONTROL,
]


MIOT_MAPPING = {
    DOOYA_CURTAIN_M1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    DOOYA_CURTAIN_M2: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    DOOYA_CURTAIN_C1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_STEPPING_UP: 3,
        ATTR_STEPPING_DOWN: 4,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    NOVO_CURTAIN_N21: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 6},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 7},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 1,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    BABAI_CURTAIN_BB82MJ: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 3},
        ATTR_PAUSE: 0,
        ATTR_OPEN: 1,
        ATTR_CLOSE: 2,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    LESHI_CURTAIN_V0001: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 2},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 5},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 6},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
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
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
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
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    SYNIOT_CURTAIN_SYC1: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 2},
        ATTR_PAUSE: 2,
        ATTR_OPEN: 0,
        ATTR_CLOSE: 1,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
    PTX_CURTAIN_SIDT82: {
        ATTR_MOTOR_CONTROL: {"siid": 2, "piid": 1},
        ATTR_CURRENT_POSITION: {"siid": 2, "piid": 2},
        ATTR_TARGET_POSITION: {"siid": 2, "piid": 2},
        ATTR_PAUSE: 1,
        ATTR_OPEN: 2,
        ATTR_CLOSE: 0,
        ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
    },
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Optional(CONF_MODEL): cv.string,
    }
)


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
        raise RuntimeError("Failing requesting {}".format(url))

    return json.loads(r.content)


def get_service(model, services):
    device_type = model.split(".")[1]
    name = "service:{}:".format(device_type)

    curtain_services = [
        service for service in services if name in service["type"]
    ]

    if len(curtain_services) == 0:
        raise RuntimeError("Current device is not a curtain: {}".format(model))

    return curtain_services[0]


def get_property(properties, name):
    name = "property:{}:".format(name)
    return [prop for prop in properties if name in prop["type"]][0]


def get_value(value_list, name_list):
    return [
        value for value in value_list if value["description"] in name_list
    ][0]["value"]


def get_mapping(model, mapping):
    """
    Populate curtain mapping from miot spec rest service.
    """
    instance_url = "https://miot-spec.org/miot-spec-v2/instances?status=all"
    instances = send_http_req(instance_url)["instances"]

    model_instances = [
        instance for instance in instances if instance["model"] == model
    ]

    if len(model_instances) == 0:
        raise RuntimeError("Failing find model: {} from internet".format(model))

    services_url = (
        "https://miot-spec.org/miot-spec-v2/instance?type={}".format(
            model_instances[0]["type"]
        )
    )

    services = send_http_req(services_url)["services"]

    curtain_service = get_service(model, services)
    siid = curtain_service["iid"]
    curtain_properties = curtain_service["properties"]

    motor_control_prop = get_property(curtain_properties, ATTR_MOTOR_CONTROL)
    mapping[ATTR_MOTOR_CONTROL]["siid"] = siid
    mapping[ATTR_MOTOR_CONTROL]["piid"] = motor_control_prop["iid"]

    value_list = motor_control_prop["value-list"]
    mapping[ATTR_PAUSE] = get_value(value_list, [ATTR_PAUSE])
    mapping[ATTR_OPEN] = get_value(value_list, [ATTR_OPEN, ATTR_UP])
    mapping[ATTR_CLOSE] = get_value(value_list, [ATTR_CLOSE, ATTR_DOWN])

    if ATTR_LUMI in model:
        status_prop = get_property(curtain_properties, ATTR_STATUS)
        mapping[ATTR_STATUS]["siid"] = siid
        mapping[ATTR_STATUS]["piid"] = status_prop["iid"]

        status_value_list = status_prop["value-list"]
        mapping[ATTR_STOPPED] = get_value(status_value_list, [ATTR_STOPPED])
        mapping[ATTR_OPENING] = get_value(status_value_list, [ATTR_OPENING])
        mapping[ATTR_CLOSING] = get_value(status_value_list, [ATTR_CLOSING])

    current_position_prop = [
        prop
        for prop in curtain_properties
        if ATTR_CURRENT_POSITION in prop["type"]
    ][0]

    mapping[ATTR_CURRENT_POSITION]["siid"] = siid
    mapping[ATTR_CURRENT_POSITION]["piid"] = current_position_prop["iid"]

    target_position_prop = [
        prop
        for prop in curtain_properties
        if ATTR_TARGET_POSITION in prop["type"]
    ][0]

    mapping[ATTR_TARGET_POSITION]["siid"] = siid
    mapping[ATTR_TARGET_POSITION]["piid"] = target_position_prop["iid"]

    if ATTR_LEGACY_PROPS not in mapping:
        mapping[ATTR_LEGACY_PROPS] = DEFAULT_LEGACY_PROPS

    return mapping


class MijiaCurtain(CoverEntity):
    def __init__(self, name, host, token, model):
        self._unique_id = name
        self._name = name
        self._current_position = 0
        self._target_position = 0
        self._action = 0

        self._host = host
        self._token = token
        self._model = model
        self._use_legacy = False

        self.miotDevice = None
        self._device = None

        if model:
            if model not in MIOT_MAPPING:
                raise RuntimeError("Unsupported model: {}".format(model))

            self._mapping = MIOT_MAPPING[model]
        else:
            self._mapping = {
                ATTR_MOTOR_CONTROL: {"siid": 0, "piid": 0},
                ATTR_CURRENT_POSITION: {"siid": 0, "piid": 0},
                ATTR_TARGET_POSITION: {"siid": 0, "piid": 0},
                ATTR_PAUSE: 0,
                ATTR_OPEN: 0,
                ATTR_CLOSE: 0,
                ATTR_LEGACY_PROPS: DEFAULT_LEGACY_PROPS,
            }

        # 优先初始化 MIOT 设备，保持老代码逻辑
        try:
            self.miotDevice = MiotDevice(
                ip=host,
                token=token,
                mapping=self._mapping,
            )
            _LOGGER.info(
                "Init miot device: %s, %s",
                self._name,
                self.miotDevice,
            )
        except Exception:
            _LOGGER.warning(
                "Init miot device failed, will try legacy miio device",
                exc_info=True,
            )
            self._use_legacy = True

        # 初始化 legacy miio 设备，作为 fallback
        try:
            self._device = MiioDevice(ip=host, token=token)
            _LOGGER.info(
                "Init legacy miio device: %s, %s",
                self._name,
                self._device,
            )
        except Exception:
            _LOGGER.warning(
                "Init legacy miio device failed",
                exc_info=True,
            )

        # 如果 model 未配置，尝试从设备读取 model，然后动态获取 mapping
        if not model:
            try:
                if self.miotDevice:
                    self._model = self.miotDevice.info().model
                elif self._device:
                    self._model = self._device.info().model
                else:
                    raise RuntimeError("No available device instance")

                self._mapping = get_mapping(self._model, self._mapping)

                if self.miotDevice:
                    self.miotDevice.mapping = self._mapping

            except Exception:
                _LOGGER.error(
                    "Get device model or mapping failed",
                    exc_info=True,
                )

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
        return self._current_position * 20

    @property
    def device_class(self) -> Optional[str]:
        if self._model == DOOYA_CURTAIN_C1:
            return CoverDeviceClass.BLIND
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
            "current_position": self._current_position,
            "target_position": self._target_position,
        }

        if self._model == DOOYA_CURTAIN_C1:
            data["current_tilt_position"] = self.current_cover_tilt_position

        return data

    @property
    def supported_features(self):
        curtain_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

        blind_features = (
            curtain_features
            | CoverEntityFeature.OPEN_TILT
            | CoverEntityFeature.CLOSE_TILT
            | CoverEntityFeature.SET_TILT_POSITION
        )

        if self._model == DOOYA_CURTAIN_C1:
            return blind_features

        return curtain_features

    @property
    def is_opening(self):
        if ATTR_LUMI in self._model:
            return self._action == self._mapping.get(ATTR_OPENING)

        return self._action == self._mapping.get(ATTR_OPEN)

    @property
    def is_closing(self):
        if ATTR_LUMI in self._model:
            return self._action == self._mapping.get(ATTR_CLOSING)

        return self._action == self._mapping.get(ATTR_CLOSE)

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

        _LOGGER.debug(
            "update_state %s data: %s",
            self._name,
            self.state_attributes,
        )

    def update_current_position(self):
        position = self.get_property(ATTR_CURRENT_POSITION)

        if position is None:
            return

        if self._model != DOOYA_CURTAIN_C1:
            if 0 < position < 5:
                position = 0

            if 95 < position < 100:
                position = 100

        self._current_position = position

    def update_target_position(self):
        position = self.get_property(ATTR_TARGET_POSITION)

        if position is not None:
            self._target_position = position

    def update_action(self):
        if ATTR_LUMI in self._model and ATTR_STATUS in self._mapping:
            action = self.get_property(ATTR_STATUS)
        else:
            action = self.get_property(ATTR_MOTOR_CONTROL)

        if action is not None:
            self._action = action

    def open_cover(self, **kwargs) -> None:
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_OPEN])

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.async_add_executor_job(
            ft.partial(self.open_cover, **kwargs)
        )

    def close_cover(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_CLOSE])

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self.hass.async_add_executor_job(
            ft.partial(self.close_cover, **kwargs)
        )

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
        self.set_property(ATTR_TARGET_POSITION, kwargs["position"])

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        await self.hass.async_add_executor_job(
            ft.partial(self.set_cover_position, **kwargs)
        )

    def stop_cover(self, **kwargs):
        self.set_property(ATTR_MOTOR_CONTROL, self._mapping[ATTR_PAUSE])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.async_add_executor_job(
            ft.partial(self.stop_cover, **kwargs)
        )

    def open_cover_tilt(self, **kwargs) -> None:
        self.set_property(
            ATTR_MOTOR_CONTROL,
            self._mapping[ATTR_STEPPING_UP],
        )

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt."""
        await self.hass.async_add_executor_job(
            ft.partial(self.open_cover_tilt, **kwargs)
        )

    def close_cover_tilt(self, **kwargs):
        self.set_property(
            ATTR_MOTOR_CONTROL,
            self._mapping[ATTR_STEPPING_DOWN],
        )

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt."""
        await self.hass.async_add_executor_job(
            ft.partial(self.close_cover_tilt, **kwargs)
        )

    def set_cover_tilt_position(self, **kwargs):
        tilt = kwargs["tilt_position"]
        position = int((100 - tilt) / 20)

        _LOGGER.debug(
            "Convert tilt to position, tilt: %s, position: %s",
            tilt,
            position,
        )

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

    def send_command(self, command, params):
        """
        Send legacy miio command.
        """
        if not self._device:
            _LOGGER.warning("Legacy miio device is not initialized")
            return None

        try:
            result = self._device.send(command, params)
            _LOGGER.debug(
                "Legacy command %s(%s) result: %s",
                command,
                params,
                result,
            )
            return result
        except Exception:
            _LOGGER.error(
                "Send legacy command %s exception",
                command,
                exc_info=True,
            )
            return None

    def set_property(self, property_key, value):
        """
        Set property by MIOT first, fallback to legacy miio protocol.

        MIOT:
            set_property_by(siid, piid, value)

        Legacy:
            motor-control   -> setOperation(value)
            target-position -> setPosition(value)
        """
        if not self._use_legacy and self.miotDevice:
            try:
                siid = self._mapping[property_key]["siid"]
                piid = self._mapping[property_key]["piid"]

                result = self.miotDevice.set_property_by(
                    siid,
                    piid,
                    value,
                )

                _LOGGER.debug(
                    "MIOT set property %s=%s result: %s",
                    property_key,
                    value,
                    result,
                )

                return result

            except Exception:
                _LOGGER.warning(
                    "MIOT set property %s=%s failed, fallback to legacy",
                    property_key,
                    value,
                    exc_info=True,
                )
                self._use_legacy = True

        return self.set_property_legacy(property_key, value)

    def set_property_legacy(self, property_key, value):
        """
        Legacy protocol fallback.

        不写死 open / close / pause 的值。
        value 由 self._mapping 传入。
        """
        if property_key == ATTR_MOTOR_CONTROL:
            return self.send_command("setOperation", [value])

        if property_key == ATTR_TARGET_POSITION:
            return self.send_command("setPosition", [value])

        _LOGGER.warning(
            "Legacy set_property unsupported property: %s=%s",
            property_key,
            value,
        )

        return None

    def get_property(self, property_key):
        """
        Get property by MIOT first, fallback to legacy miio protocol.
        """
        value = None

        if not self._use_legacy and self.miotDevice:
            try:
                siid = self._mapping[property_key]["siid"]
                piid = self._mapping[property_key]["piid"]

                results = self.miotDevice.get_property_by(siid, piid)

                for result in results:
                    if (
                        result.get("code") == 0
                        and result.get("siid") == siid
                        and result.get("piid") == piid
                    ):
                        value = result.get("value")
                        break

                _LOGGER.debug(
                    "%s, MIOT %s is: %s",
                    self._name,
                    property_key,
                    value,
                )

                if value is not None:
                    return value

            except Exception:
                _LOGGER.warning(
                    "MIOT get property %s failed, fallback to legacy",
                    property_key,
                    exc_info=True,
                )
                self._use_legacy = True

        value = self.get_property_legacy(property_key)

        _LOGGER.debug(
            "%s, legacy %s is: %s",
            self._name,
            property_key,
            value,
        )

        return value

    def get_property_legacy(self, property_key):
        """
        Legacy get_prop fallback.

        默认 legacy 返回顺序：
            current-position, target-position, motor-control

        如果某个型号返回顺序不同，可以在 MIOT_MAPPING 对应 model 中增加：
            ATTR_LEGACY_PROPS: [...]
        """
        legacy_props = self._mapping.get(
            ATTR_LEGACY_PROPS,
            DEFAULT_LEGACY_PROPS,
        )

        legacy_property_key = property_key

        if property_key == ATTR_STATUS:
            legacy_property_key = ATTR_MOTOR_CONTROL

        if legacy_property_key not in legacy_props:
            _LOGGER.warning(
                "Unknown legacy property key: %s",
                property_key,
            )
            return None

        prop_index = legacy_props.index(legacy_property_key)

        try:
            prop_ids = list(range(len(legacy_props)))
            results = self.send_command("get_prop", prop_ids)

            if (
                results
                and isinstance(results, list)
                and len(results) > prop_index
            ):
                return results[prop_index]

        except Exception:
            _LOGGER.error(
                "Legacy get property %s exception",
                property_key,
                exc_info=True,
            )

        return None
