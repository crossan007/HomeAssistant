from charles_dev.daikin_device import DaikinDevice
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import _LOGGER, DOMAIN


class DaikinEntity(Entity):
    """Base class for Daikin stuff."""

    _attr_has_entity_name = True

    def __init__(self, device: DaikinDevice) -> None:
        self._device = device
        self._attr_unique_id = device.mac

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.mac)},
            name=device.name,
            manufacturer="Daikin",
        )
        device.add_update_callback(self.on_data_updated)

    def on_data_updated(self):
        """Callback from the DaikinDevice class when the data model changes."""
        _LOGGER.debug("Device Data updated:")
        self._attr_device_info["model"] = self._device.device_data.manufacturer.text
        self._attr_device_info["name"] = self._device.device_data.name
        self.async_schedule_update_ha_state()
