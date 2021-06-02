from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError, BusType

from ofono2mm.mm_modem_3gpp import MMModem3gppInterface
from ofono2mm.mm_modem_messaging import MMModemMessagingInterface
from ofono2mm.mm_sim import MMSimInterface

class MMBearerInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Bearer')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
                "Interface": Variant('s', ''),
                "Connected": Variant('b', False),
                "Suspended": Variant('b', False),
                "Ip4Config": Variant('a{sv}', {}),
                "Ip6Config": Variant('a{sv}', {}),
                "IpTimeout": Variant('u', 0),
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
    def Properties(self) -> 'a{sv}':
        return self.props['Properties'].value

    @method()
    def Connect(self):
        pass

    @method()
    def Disconnect(self):
        pass
