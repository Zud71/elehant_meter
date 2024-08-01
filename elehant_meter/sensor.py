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
    UnitOfVolume
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .const import log
from .const import MeterType
from .const import counters_mac


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
        native_unit_of_measurement= UnitOfVolume.CUBIC_METERS,
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
}


def _device_key_to_bluetooth_entity_desc(   
    device: BLEDevice,
    key: str,
    desc:ElehantSensorEntityDescription,
    ) -> ElehantSensorEntityDescription:
    """Замена типа счетчика"""

    mac = device.address.lower()
    result = desc
    metertype: MeterType = None    

    if key=="meter_reading":
        for key in counters_mac:
            has_mac = mac[0:8] in counters_mac[key]
            if has_mac :          
                metertype = key
                break
    
    assert metertype is not None, "Неизвестное устройство"
        
    if metertype != MeterType.GAS :
       result.device_class=SensorDeviceClass.WATER

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
    hass_device_info = DeviceInfo({})

    return hass_device_info


def sensor_update_to_bluetooth_data_update(
    adv: ElehantData,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a Bluetooth data update."""
    
    result =  PassiveBluetoothDataUpdate(
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
    return result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Elehant sensors."""

    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)

    entry.async_on_unload(processor.async_add_entities_listener(ElehantBluetoothSensorEntity, async_add_entities))
    
    entry.async_on_unload(coordinator.async_register_processor(processor))


class ElehantBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[PassiveBluetoothDataProcessor[float | int | None,ElehantData]],
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

    #@property
    #def icon(self):
        #return {"icon": "mdi:alarm-bell"}.get("icon")

