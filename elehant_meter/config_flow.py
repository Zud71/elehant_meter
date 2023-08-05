"""Config flow for Elehant integration."""
from __future__ import annotations

import logging
from typing import Any

from .const import ElehantData

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
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

        adv = self._discovered_device

        title = adv.name 
        if user_input is not None:
            return self.async_create_entry(title=title, data={})

        self._set_confirm_only()
        placeholders = {"name": title}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders=placeholders
        )