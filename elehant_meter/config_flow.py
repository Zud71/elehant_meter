"""Config flow for Elehant integration."""
from __future__ import annotations

import logging
from typing import Any

from .const import ElehantData
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import AbortFlow, FlowResult

from .const import DOMAIN
from .const import log

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

        _LOGGER.debug("Discovered BT device: %s", discovery_info)

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        adv = ElehantData(discovery_info.device, discovery_info.advertisement)


        self._discovery_info = discovery_info

        self._discovered_device = adv
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        assert self._discovered_device is not None
        adv = self._discovered_device

        title = adv.name 
        assert title is None, "Ошибка: Пустой заголовок"

        if user_input is not None:
            return self.async_create_entry(title=title, data={})

        assert title is not None

        self._set_confirm_only()
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders=placeholders
        )
    

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
            if adv.manufacturer_data:
                self._discovered_devices[address] = (
                    adv.readings.name if adv.readings else discovery_info.name,
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
