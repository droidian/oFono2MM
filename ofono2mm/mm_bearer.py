from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError, BusType

from ofono2mm.mm_modem_3gpp import MMModem3gppInterface
from ofono2mm.mm_modem_messaging import MMModemMessagingInterface
from ofono2mm.mm_sim import MMSimInterface

from ofono2mm.utils import async_retryable

import asyncio

class MMBearerInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Bearer')
        print("Creating new bearer interface for %i", index)
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.mm_modem = mm_modem
        self.disconnecting = False
        self.reconnect_task = None
        self.props = {
                "Interface": Variant('s', ''),
                "Connected": Variant('b', False),
                "Suspended": Variant('b', False),
                "Ip4Config": Variant('a{sv}', {
                    "method": Variant('u', 3)
                }),
                "Ip6Config": Variant('a{sv}', {
                    "method": Variant('u', 3)
                }),
                "IpTimeout": Variant('u', 0),
                "BearerType": Variant('u', 1),
                "Properties": Variant('a{sv}', {})
        }

    @dbus_property(access=PropertyAccess.READ)
    def Interface(self) -> 's':
        return self.props['Interface'].value

    @dbus_property(access=PropertyAccess.READ)
    def Connected(self) -> 'b':
        return self.props['Connected'].value

    @dbus_property(access=PropertyAccess.READ)
    def Suspended(self) -> 'b':
        return self.props['Suspended'].value

    @dbus_property(access=PropertyAccess.READ)
    def Ip4Config(self) -> 'a{sv}':
        return self.props['Ip4Config'].value

    @dbus_property(access=PropertyAccess.READ)
    def Ip6Config(self) -> 'a{sv}':
        return self.props['Ip6Config'].value

    @dbus_property(access=PropertyAccess.READ)
    def IpTimeout(self) -> 'u':
        return self.props['IpTimeout'].value

    @dbus_property(access=PropertyAccess.READ)
    def BearerType(self) -> 'u':
        return self.props['BearerType'].value

    @dbus_property(access=PropertyAccess.READ)
    def Properties(self) -> 'a{sv}':
        return self.props['Properties'].value

    @method()
    async def Connect(self):
        await self.doConnect()

    @async_retryable()
    async def doConnect(self):
        print("Do connect")
        ofono_ctx_interface = self.ofono_client["ofono_context"][self.ofono_ctx]['org.ofono.ConnectionContext']
        await ofono_ctx_interface.call_set_property("Active", Variant('b', True))

        # Clear the reconnection task
        self.reconnect_task = None

    @method()
    async def Disconnect(self):
        await self.doDisconnect()

    async def cancel_reconnect_task(self):
        if self.reconnect_task is not None:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                # Finally
                pass
            finally:
                self.reconnect_task = None

    async def doDisconnect(self):
        self.disconnecting = True

        # Cancel an eventual reconnection task
        await self.cancel_reconnect_task()

        ofono_ctx_interface = self.ofono_client["ofono_context"][self.ofono_ctx]['org.ofono.ConnectionContext']
        await ofono_ctx_interface.call_set_property("Active", Variant('b', False))

    async def add_auth_ofono(self, username, password):
        ofono_ctx_interface = self.ofono_client["ofono_context"][self.ofono_ctx]['org.ofono.ConnectionContext']
        await ofono_ctx_interface.call_set_property("Username", Variant('s', username))
        await ofono_ctx_interface.call_set_property("Password", Variant('s', password))

    def ofono_context_changed(self, propname, value):
        if propname == "Active":
            if self.disconnecting and (not value.value):
                self.disconnecting = False
            elif not self.disconnecting and (not value.value) and self.reconnect_task is None and self.props['Connected'].value:
                self.reconnect_task = asyncio.create_task(self.doConnect())
            self.props['Connected'] = value
            self.emit_properties_changed({'Connected': value.value})
        elif propname == "Settings":
            if 'Interface' in value.value:
                self.props['Interface'] = value.value['Interface']
                self.emit_properties_changed({'Interface': value.value['Interface'].value})
                if [value.value['Interface'].value, 2] not in self.mm_modem.props['Ports'].value:
                    self.mm_modem.props['Ports'].value.append([value.value['Interface'].value, 2])
            if 'Method' in value.value:
                if value.value['Method'].value == 'static':
                    self.props['Ip4Config'].value['method'] = Variant('u', 2)
                if value.value['Method'].value == 'dhcp':
                    self.props['Ip4Config'].value['method'] = Variant('u', 3)
            if 'Address' in value.value:
                self.props['Ip4Config'].value['address'] = value.value['Address']
            if 'DomainNameServers' in value.value:
                for i in range(0, min(3, len(value.value['DomainNameServers'].value))):
                    self.props['Ip4Config'].value['dns' + str(i + 1)] = Variant('s', value.value['DomainNameServers'].value[i])
            if 'Gateway' in value.value:
                self.props['Ip4Config'].value['gateway'] = value.value['Gateway']
            self.emit_properties_changed({'Ip4Config': self.props['Ip4Config'].value})

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_props()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            self.set_props()
        return ch

