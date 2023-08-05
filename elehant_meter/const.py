"""Constants for the Elehant integration."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, NamedTuple

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


DOMAIN = "elehant_meter"

# Manufacurer id
MANUFACTURER_ID = 65535

class MeterType(IntEnum):
    GAS = 0
    WATER = 1
    WATERD = 2
    WATERT = 3

counters_mac = {
	MeterType.GAS: [
		'b0:10:01',
		'b0:11:01',
		'b0:12:01',
		'b0:32:01',
		'b0:42:01'
	],
	MeterType.WATER: [
		'b0:01:02',
		'b0:02:02'
	],
	MeterType.WATERD: [
		'b0:03:02',
		'b0:05:02'
	],
	MeterType.WATERT: [
		'b0:04:02',
		'b0:06:02'
	],
}

@dataclass
class ElehantData:

    device: BLEDevice = None
    name: str = None
    meter_reading: str = None
    temperature: str = None
    id_meter: str = None
    battery: str = None
    metertype: MeterType = None
    rssi: str = None

    def __init__(self, device=None, ad_data=None):
        self.device = device
        mac = device.address.lower()
        

        if device and ad_data:
            has_manufacurer_data = MANUFACTURER_ID in ad_data.manufacturer_data

            for key in counters_mac:
                has_mac = mac[0:8] in counters_mac[key]
                if has_mac :          
                        metertype = key
                        break 
            
            if has_manufacurer_data and has_mac:
                raw_bytes = ad_data.manufacturer_data[MANUFACTURER_ID]
                
                c_num = int.from_bytes(raw_bytes[6:9], byteorder='little')
                c_count = int.from_bytes(raw_bytes[9:13], byteorder='little')
                c_temp = int.from_bytes(raw_bytes[14:16], byteorder="little") / 100

                self.id_meter =str(c_num)
                self.name = "Cчетчик "
                if metertype == MeterType.GAS :
                    self.name += "газа: "
                else:  self.name += "воды: "
                
                self.name +=  str(c_num)
                self.meter_reading = str(c_count/10000)
                self.temperature = str(c_temp)
                self.rssi = ad_data.rssi



def log(data) -> None:

    my_file = open("elehant_meter.log", "a")
    my_file.writelines(data + "\n")
    my_file.close()
