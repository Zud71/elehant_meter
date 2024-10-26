"""Config flow for Elehant integration."""
from __future__ import annotations

import logging
from typing import Any

from .const import ElehantData
from .const import MANUFACTURER_ID
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import AbortFlow, FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elehant."""

    def __init__(self) -> None:
        """Set up a new config flow for Elehant."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: ElehantData | None = None
        self._discovered_devices: dict[str, tuple[str, ElehantData]] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the Bluetooth discovery step."""

        _LOGGER.debug("Обнаружено устройство BT: %s", discovery_info)
        _LOGGER.debug("Данные в HEX: %s", discovery_info.manufacturer_data[MANUFACTURER_ID].hex().upper())

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        adv = ElehantData(discovery_info.device, discovery_info.advertisement)
        
        if not adv.macdata.signValid:
            _LOGGER.debug("Обнаружено неподдерживаемое устройство: %s", discovery_info)
            return self.async_abort(reason="not_supported")

        self._discovery_info = discovery_info

        self._discovered_device = adv
        return await self.async_step_bluetooth_confirm()
            

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        assert self._discovered_device is not None
        adv = self._discovered_device

        _LOGGER.debug("async_step_bluetooth_confirm: %s", adv)

        if adv.macdata.signValid:
            title = adv.name
            assert title is not None, "Ошибка: Пустой заголовок"

            if user_input is not None:
                return self.async_create_entry(title=title, data={})

            self._set_confirm_only()
            placeholders = {"name": title}
            self.context["title_placeholders"] = placeholders
            return self.async_show_form(
                step_id="bluetooth_confirm", description_placeholders=placeholders)
                
        else:
            _LOGGER.debug("Confirm discovery - не пройден: %s", adv)
            return self.async_abort(reason="not_supported")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            adv = self._discovered_devices[address][1]
            self._raise_for_advertisement_errors(adv)

            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address][0], data={}
            )

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            adv = ElehantData(
                discovery_info.device, discovery_info.advertisement
            )
            if adv.macdata.signValid:
                self._discovered_devices[address] = (
                    adv.name,
                    adv,
                )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: dev[0]
                            for (addr, dev) in self._discovered_devices.items()
                        }
                    )
                }
            ),
        )
