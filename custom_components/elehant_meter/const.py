"""Constants for the Elehant integration."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, NamedTuple

from bleak.backends.device import BLEDevice
import logging

import json

DOMAIN = "elehant_meter"
_LOGGER = logging.getLogger(__name__)

# Manufacurer id
MANUFACTURER_ID = 65535


class MeterType(IntEnum):
    GAS = 1
    WATER = 2
    ELECTRIC = 3
    HEAT = 4


MeterModel = {
	MeterType.GAS: [
            1, 2, 3, 4, 5, 16, 17, 18, 19, 20,
            32, 33, 34, 35, 36, 48, 49, 50, 51, 52,
            64, 65, 66, 67, 68, 80, 81, 82, 83, 84
        ],
	MeterType.WATER: [1, 2, 3, 4, 5, 6],
	MeterType.ELECTRIC: [],
	MeterType.HEAT: []
}

METER = {
    "1-1": "СГБ-1.8",
    "1-2": "СГБ-3.2",
    "1-3": "СГБ-4.0",
    "1-4": "СГБ-6.0",
    "1-5": "СГБ-1.6",
    "1-16": "СГБД-1.8",
    "1-17": "СГБД-3.2",
    "1-18": "СГБД-4.0",
    "1-19": "СГБД-6.0",
    "1-20": "СГБД-1.6",
    "1-32": "СОНИК-G1,6",
    "1-33": "СОНИК-G2,5",
    "1-34": "СОНИК-G4",
    "1-35": "СОНИК-G6",
    "1-36": "СОНИК-G10",
    "1-48": "СГБД-1.8ТК",
    "1-49": "СГБД-3.2ТК",
    "1-50": "СГБД-4.0ТК",
    "1-51": "СГБД-6.0ТК",
    "1-52": "СГБД-1.6ТК",
    "1-64": "СОНИК-G1,6ТК",
    "1-65": "СОНИК-G2,5ТК",
    "1-66": "СОНИК-G4ТК",
    "1-67": "СОНИК-G6ТК",
    "1-68": "СОНИК-G10ТК",
    "1-80": "СГБ-1.8ТК",
    "1-81": "СГБ-3.2ТК",
    "1-82": "СГБ-4.0ТК",
    "1-83": "СГБ-6.0ТК",
    "1-84": "СГБ-1.6ТК",
    "2-1": "СВД-15",
    "2-2": "СВД-20",
    "2-3": "СВТ-15",
    "2-4": "СВТ-15",
    "2-5": "СВТ-20",
    "2-6": "СВТ-20",
    "3-1": "СЭБ",
    "4-1": "СТБ-10"
}


@dataclass
class MacData:
    mtype: int = None
    model: int = None
    signValid: bool = False


@dataclass
class ElehantData:

    device: BLEDevice = None
    name: str = None

    meter_reading: str = None
    temperature: str = None
    rssi: str = None
    battery: int = None

    id_meter: str = None
    mtype: int = None
    model: int = None
    name_model: str = None
    frimware: str = None
    packetVer: int = None

    macdata: MacData = None

    def __init__(self, device=None, ad_data=None):
        _LOGGER.debug("ElehantData init")
        if device and ad_data:
            self.device = device
            mac = device.address.lower()

            has_manufacurer_data = MANUFACTURER_ID in ad_data.manufacturer_data

            self.macdata = parse_mac(mac)

            if self.macdata.signValid:
                self.macdata.signValid = False

                raw_bytes = ad_data.manufacturer_data[MANUFACTURER_ID]
                packetVer = int.from_bytes(raw_bytes[3:4], byteorder="little")
                
                _LOGGER.debug("Версия пакета: %s", packetVer)

                if has_manufacurer_data and packetVer == 1:
                    v_num = int.from_bytes(raw_bytes[6:9], byteorder='little')
                    v_count = int.from_bytes(raw_bytes[9:13], byteorder='little')
                    v_temp = int.from_bytes(raw_bytes[14:16], byteorder="little")
                    v_battery = int.from_bytes(raw_bytes[13:14], byteorder="little")
                    
                    v_mtype = int.from_bytes(raw_bytes[4:5], byteorder="little")
                    v_model = int.from_bytes(raw_bytes[5:6], byteorder="little")
                    
                    v_fw = int.from_bytes(raw_bytes[16:17], byteorder="little")

                    if v_mtype == self.macdata.mtype and v_model == self.macdata.model:

                        v_count = v_count/10000
                        v_temp = v_temp/100
                        v_battery = min(v_battery, 100)

                        key_name = str(v_mtype) + "-" + str(v_model)
                        v_name_model = METER[key_name]

                        self.name = "Счетчик "
                        if v_mtype == MeterType.GAS:
                            self.name += "газа "
                        if v_mtype == MeterType.WATER:
                            self.name += "воды "
                        if v_mtype == MeterType.ELECTRIC:
                            self.name += "электричества "
                        if v_mtype == MeterType.HEAT:
                            self.name += "тепла "

                        v_num = '{:07}'.format(v_num)
                        self.name += v_name_model + ": " + v_num

                        self.id_meter = v_num
                        self.name_model = v_name_model
                        self.meter_reading = str(v_count)
                        self.temperature = str(v_temp)
                        self.battery = v_battery
                        self.mtype = v_mtype
                        self.model = v_model
                        self.frimware = v_fw/10
                        self.rssi = ad_data.rssi

                        self.macdata.signValid = True


                        _LOGGER.debug("Имя устройства: %s", self.name)
                        _LOGGER.debug("MAC: %s", mac)
                        _LOGGER.debug("ID: %s", self.id_meter)
                        _LOGGER.debug("Модель: %s", self.name_model)
                        _LOGGER.debug("Показания: %s", self.meter_reading)
                        _LOGGER.debug("Темперетара: %s", self.temperature)
                        _LOGGER.debug("Батарея: %s", self.battery)
                        _LOGGER.debug("Сигнал: %s", self.rssi)

                        _LOGGER.debug("Тип мас: %s", self.mtype)
                        _LOGGER.debug("Модель мас: %s", self.model)
                        _LOGGER.debug("Версия прошивки: %s", self.frimware)

                else:
                    self.macdata.signValid = False
                    _LOGGER.debug(
                        "ElehantData init - не пройдена проверка по производителю или версии пакета MAC %s", mac)
        else:
            self.macdata.signValid = False
            _LOGGER.debug(
                "ElehantData init - не пройдена, device или ad_data пустые")


def parse_mac(in_mac) -> MacData:
    result = MacData(None, None, False)
    mac = str(in_mac)

    _LOGGER.debug("parse_mac: %s", mac)

    if mac[0:2] == "b0":
        result.mtype = int(mac[6:8], 16)
        result.model = int(mac[3:5], 16)

        if (result.mtype == MeterType.GAS and result.model in MeterModel[MeterType.GAS]) or (result.mtype == MeterType.WATER and result.model in MeterModel[MeterType.WATER]):
            result.signValid = True
    else:
        if mac[0:2] == "b1":
            _LOGGER.debug(
                "parse_mac Устройство Елехант (B1). Данные не расшифрованны, игнорирование, результат: %s", mac[0:2])
        else:
            _LOGGER.debug(
                "parse_mac Устройство не Елехант только (B0 или В1) , результат: %s", mac[0:2])

    _LOGGER.debug("parse_mac signValid: %s", result.signValid)
    return result
