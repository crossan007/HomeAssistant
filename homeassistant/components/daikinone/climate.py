"""Support for DaikinNA Cloud climate systems."""

from typing import Any

from charles_dev.daikin_device import DaikinDevice
from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import DaikinData
from .const import _LOGGER, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Daikin device."""
    cool_away_temp = 80  # entry.options.get(CONF_COOL_AWAY_TEMPERATURE)
    heat_away_temp = 50  # entry.options.get(CONF_HEAT_AWAY_TEMPERATURE)

    data: DaikinData = hass.data[DOMAIN][entry.entry_id]

    _LOGGER.debug("Initializing Daikin climate devices: %s", data.client.profile.email)

    async_add_entities(
        [
            DaikinNADevice(device, cool_away_temp, heat_away_temp)
            for device in data.client.devices
        ]
    )


DKN_MODE_TO_HVAC_MODE = {
    5: HVACMode.DRY,
    4: HVACMode.FAN_ONLY,
    3: HVACMode.HEAT,
    2: HVACMode.COOL,
    1: HVACMode.HEAT_COOL,
}

DKN_MODE_TO_FAN_MODE = {0: FAN_AUTO, 2: FAN_LOW, 4: FAN_MEDIUM, 6: FAN_HIGH}


class DaikinNADevice(ClimateEntity):
    """Representation of a DaikinNA Device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device: DaikinDevice,
        cool_away_temp: int | None,
        heat_away_temp: int | None,
    ) -> None:
        self._device = device
        self._cool_away_temp = cool_away_temp
        self._heat_away_temp = heat_away_temp
        self._away = False

        self._attr_unique_id = device.mac

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.mac)},
            name=device.name,
            manufacturer="Daikin",
        )

        self._attr_hvac_modes = list(DKN_MODE_TO_HVAC_MODE.values())
        self._attr_hvac_modes.append(HVACMode.OFF)

        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        _LOGGER.debug(
            "Created DaikinNADevice '%s':'%s'", self._device.mac, self._device.name
        )

        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )

        device.set_update_callback(self.on_data_updated)

    def _hvac_mode_to_dkn_mode(self, hvac_mode: HVACMode) -> int:
        return list(DKN_MODE_TO_HVAC_MODE.keys())[
            list(DKN_MODE_TO_HVAC_MODE.values()).index(hvac_mode)
        ]

    def _fan_mode_to_dkn_mode(self, fan_mode: str) -> int:
        return list(DKN_MODE_TO_FAN_MODE.keys())[
            list(DKN_MODE_TO_FAN_MODE.values()).index(fan_mode)
        ]

    def on_data_updated(self):
        """Callback from the DaikinDevice class when the data model changes."""
        _LOGGER.debug("Device Data updated:")
        self._attr_device_info["model"] = self._device.device_data.manufacturer.text
        self._attr_device_info["name"] = self._device.device_data.name
        self.schedule_update_ha_state(True)

    @property
    def name(self):
        """Name of the entity."""
        return self._device.name

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        if self._device.device_data.power is False:
            return HVACMode.OFF
        else:
            return DKN_MODE_TO_HVAC_MODE.get(self._device.device_data.real_mode)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        if self._device.device_data.power is False:
            return HVACMode.OFF
        else:
            return DKN_MODE_TO_HVAC_MODE[self._device.device_data.mode]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.device_data.work_temp

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVACMode.COOL:
            return self._device.device_data.setpoint_air_cool
        if self.hvac_mode == HVACMode.HEAT:
            return self._device.device_data.setpoint_air_heat
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._device.device_data.setpoint_air_auto
        return None

    @property
    def fan_mode(self) -> str:
        return DKN_MODE_TO_FAN_MODE[self._device.device_data.speed_state]

    @property
    def fan_modes(self) -> list[str]:
        return list(DKN_MODE_TO_FAN_MODE.values())

    @property
    def available(self) -> bool:
        return (
            self._device.device_data.isConnected
            and self._device.device_data.machineready
        )

    @property
    def sw_version(self) -> str:
        return self._device.device_data.version

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        current_power_state = self._device.device_data.power is True
        new_power_state = hvac_mode != HVACMode.OFF
        if new_power_state is True:
            await self._device.set_device_value(
                "mode", self._hvac_mode_to_dkn_mode(hvac_mode)
            )
        if new_power_state != current_power_state:
            await self._device.set_device_value("power", new_power_state)
            self.schedule_update_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._device.set_device_value(
            "speed_state", self._fan_mode_to_dkn_mode(fan_mode)
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            raise UpdateFailed("No target temperature specified")
        property_to_update = ""
        if self.hvac_mode == HVACMode.COOL:
            property_to_update = "setpoint_air_cool"
        elif self.hvac_mode == HVACMode.HEAT:
            property_to_update = "setpoint_air_heat"
        elif self.hvac_mode == HVACMode.HEAT_COOL:
            property_to_update = "setpoint_air_auto"
        else:
            raise UpdateFailed("Invalid hvac_mode:  %s")
        try:
            await self._device.set_device_value(property_to_update, temperature)
        except Exception:
            raise UpdateFailed("set_temperature update failed")
