from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError, BusType

from ofono2mm.mm_modem_3gpp import MMModem3gppInterface
from ofono2mm.mm_modem_messaging import MMModemMessagingInterface
from ofono2mm.mm_sim import MMSimInterface

class MMBearerInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Bearer')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.mm_modem = mm_modem
        self.props = {
                "Interface": Variant('s', 'ccmni0'),
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

    async def doConnect(self):
        with open('/usr/lib/ofono2mm/ofono_context.xml', 'r') as f:
            ctx_introspection = f.read()
        ofono_ctx_object = self.bus.get_proxy_object('org.ofono', self.ofono_ctx, ctx_introspection)
        ofono_ctx_interface = ofono_ctx_object.get_interface('org.ofono.ConnectionContext')
        await ofono_ctx_interface.call_set_property("Active", Variant('b', True))

    @method()
    async def Disconnect(self):
        await self.doDisconnect()

    async def doDisconnect(self):
        with open('/usr/lib/ofono2mm/ofono_context.xml', 'r') as f:
            ctx_introspection = f.read()
        ofono_ctx_object = self.bus.get_proxy_object('org.ofono', self.ofono_ctx, ctx_introspection)
        ofono_ctx_interface = ofono_ctx_object.get_interface('org.ofono.ConnectionContext')
        await ofono_ctx_interface.call_set_property("Active", Variant('b', False))

    def ofono_context_changed(self, propname, value):
        if propname == "Active":
            self.props['Connected'] = value
            self.emit_properties_changed({'Connected': value.value})
        if propname == "Settings":
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

