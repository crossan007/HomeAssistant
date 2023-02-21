"""Non-climate data from Daikin Cloud."""
from __future__ import annotations

from typing import Any

from charles_dev.daikin_device import DaikinDevice
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaikinData
from .const import DOMAIN

SENSOR_DEVICE_CLASS_ICON_MAP: dict[str, dict[str, Any]] = {
    hc.SENSOR_STATUS_RSSI: {
        ICON: "mdi:access-point",
        STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    hc.SENSOR_STATUS_SSID: {ICON: "mdi:access-point-network"},
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Daikin Sensor."""
    data: DaikinData = hass.data[DOMAIN][config_entry.entry_id]
    sensors = []

    for device in data.client.devices:
        # for description in SENSOR_TYPES:
        #    if getattr(device, description.key) is not None:
        sensors.append(DaikinSensor(device))

    async_add_entities(sensors)


class DaikinSensor(SensorEntity):
    entity_description = "Wifi status"
    _attr_has_entity_name = True

    def __init__(self, device: DaikinDevice) -> None:
        self.state_class = SensorStateClass.MEASUREMENT
