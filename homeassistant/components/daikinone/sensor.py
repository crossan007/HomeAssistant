"""Non-climate data from Daikin Cloud."""
from __future__ import annotations

from dataclasses import dataclass

from charles_dev.daikin_device import DaikinDevice
from homeassistant.components.daikinone.entity import DaikinEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaikinData
from .const import DOMAIN


@dataclass
class DaikinSensorEntityDescription(SensorEntityDescription):
    daikin_property_name: str | None = None


SENSORS: list[DaikinSensorEntityDescription] = [
    DaikinSensorEntityDescription(
        key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        name="RSSI",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        daikin_property_name="stat_rssi",
    ),
    DaikinSensorEntityDescription(
        key="ssid",
        name="SSID",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        daikin_property_name="stat_ssid",
    ),
    DaikinSensorEntityDescription(
        key="channel",
        name="Channel",
        entity_registry_enabled_default=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        daikin_property_name="stat_channel",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Daikin Sensor."""
    data: DaikinData = hass.data[DOMAIN][config_entry.entry_id]
    sensor_entities = []

    for device in data.client.devices:
        for sensor in SENSORS:
            sensor_class = DaikinNASensor(device, sensor)
            sensor_entities.append(sensor_class)

    async_add_entities(sensor_entities)


class DaikinNASensor(DaikinEntity, SensorEntity):
    """Sensor class for Daikin."""

    _attr_has_entity_name = True
    daikin_property_name: str

    def __init__(
        self, device: DaikinDevice, description: DaikinSensorEntityDescription
    ) -> None:
        self.entity_description = description
        self.daikin_property_name = description.daikin_property_name
        super().__init__(device=device)
        self._attr_unique_id = f"{self._device.mac}-{description.key}"

    def on_data_updated(self):
        self._attr_native_value = getattr(
            self._device.device_data, self.daikin_property_name
        )
