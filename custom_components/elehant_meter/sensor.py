"""Support for Elehant sensors."""
from __future__ import annotations

from dataclasses import dataclass

from .const import ElehantData
from bleak.backends.device import BLEDevice

from homeassistant import config_entries
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfPower
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .const import MeterType
from .const import MacData
from .const import parse_mac

import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class ElehantSensorEntityDescription(SensorEntityDescription):
    """Class to describe an Elehant sensor entity."""
    name: str | None = None


SENSOR_DESCRIPTIONS = {
    "temperature": ElehantSensorEntityDescription(
        key="temperature",
        name="Температура",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "meter_reading": ElehantSensorEntityDescription(
        key="meter_reading",
        name="Показания",
        device_class=SensorDeviceClass.GAS,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL,
    ),
    "battery": ElehantSensorEntityDescription(
        key="battery",
        name="Батарея",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "rssi": ElehantSensorEntityDescription(
        key="rssi",
        name="Сигнал",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "timestamp": ElehantSensorEntityDescription(
        key="timestamp",
        name="Обновлено",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:invoice-clock-outline",
    ),
}


def _device_key_to_bluetooth_entity_desc(
    device: BLEDevice,
    key: str,
    desc: ElehantSensorEntityDescription,
) -> ElehantSensorEntityDescription:
    """Замена типа счетчика"""

    _LOGGER.debug("_device_key_to_bluetooth_entity_desc")

    mac = device.address.lower()
    result = desc

    # _LOGGER.debug("MAC: %s", mac)
    # _LOGGER.debug("KEY: %s", key)

    if key == "meter_reading":
        _LOGGER.debug("MAC: %s", mac)
        _LOGGER.debug("KEY: %s", key)

        macdata = parse_mac(mac)

        _LOGGER.debug("metertype: %s", macdata.mtype)

        assert macdata.signValid is not None, "Неизвестное устройство"

        if macdata.mtype == MeterType.GAS:
            result.device_class = SensorDeviceClass.GAS
            _LOGGER.debug("Выбран тип: GAS")

        if macdata.mtype == MeterType.WATER:
            _LOGGER.debug("Выбран тип: WATER")
            result.device_class = SensorDeviceClass.WATER
            result.name = "Вода хол"

            if macdata.model == 4 or macdata.model == 6:
               result.key= "meter_reading_second"
               result.name="Вода гор"            
            
        if macdata.mtype == MeterType.ELECTRIC:  
            result.device_class = SensorDeviceClass.ENERGY
            result.native_unit_of_measurement = UnitOfPower.KILO_WATT_HOUR
            _LOGGER.debug("Выбран тип: ELECTRIC")
        if macdata.mtype == MeterType.HEAT:
            result.device_class = SensorDeviceClass.ENERGY
            result.native_unit_of_measurement = "Gcal"
            _LOGGER.debug("Выбран тип: HEAT")

    return result


def _device_key_to_bluetooth_entity_key(
    device: BLEDevice,
    key: str,
) -> PassiveBluetoothEntityKey:
    """Convert a device key to an entity key."""

    return PassiveBluetoothEntityKey(key, device.address)


def _sensor_device_info_to_hass(
    adv: ElehantData,
) -> DeviceInfo:
    """Convert a sensor device info to hass device info."""
    hass_device_info = DeviceInfo(
        name = adv.name,
        serial_number=adv.id_meter,
       # model_id=adv.device.address,
        model = adv.name_model,
        hw_version=adv.frimware,
        manufacturer = "Элехант"
    )

    _LOGGER.debug("sensor_device_info_to_hass: %s", hass_device_info)
    return hass_device_info


def sensor_update_to_bluetooth_data_update(
    adv: ElehantData,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a Bluetooth data update."""
   
    result = PassiveBluetoothDataUpdate(
        devices={adv.device.address: _sensor_device_info_to_hass(adv)},
        entity_descriptions={
            _device_key_to_bluetooth_entity_key(adv.device, key): _device_key_to_bluetooth_entity_desc(adv.device, key, desc)
            for key, desc in SENSOR_DESCRIPTIONS.items()
        },
        entity_data={
            _device_key_to_bluetooth_entity_key(adv.device, key): getattr(adv, key, None)
            for key in SENSOR_DESCRIPTIONS
        },
        entity_names={
            _device_key_to_bluetooth_entity_key(adv.device, key): desc.name
            for key, desc in SENSOR_DESCRIPTIONS.items()
        },
    )
    _LOGGER.debug("sensor_update_to_bluetooth_data_update: %s", result)

    return result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Elehant sensors."""

    _LOGGER.debug("async_setup_entry: %s", entry)

    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][entry.entry_id]

    processor = PassiveBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update)

    entry.async_on_unload(processor.async_add_entities_listener(
        ElehantBluetoothSensorEntity, async_add_entities))

    entry.async_on_unload(coordinator.async_register_processor(processor))


class ElehantBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[PassiveBluetoothDataProcessor[float | int | None, ElehantData]],
    SensorEntity,
):
    """Representation of an Elehant sensor."""

    @property
    def available(self) -> bool:
        """Return whether the entity was available in the last update."""

        return (
            super().available
            and self.processor.entity_data.get(self.entity_key) is not None
        )

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""

        assert (value := self.native_value) is not None

        if (key := self.entity_key.key) == "rssi":
            if value < -85:
                value = 1

            elif value < -60:
                value = 2

            else:
                value = 3

            return f"mdi:signal-cellular-{value}"

        if key == "battery":
            if value >= 90:
                value = "high"

            elif value >= 60:
                value = "medium"

            else:
                value = "low"

            return f"mdi:battery-{value}"

        return super().icon
