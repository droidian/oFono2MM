from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next.errors import DBusError
from dbus_next import Variant, DBusError, BusType

import asyncio

class MMModem3gppInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
            'Imei': Variant('s', ofono_props['Serial'].value),
            'RegistrationState': Variant('u', 0),
            'OperatorCode': Variant('s', ''),
            'OperatorName': Variant('s', ''),
            'EnableFacilityLocks': Variant('u', 0),
            'SubscriptionState': Variant('u', 0),
            'EpsUeModeOperation': Variant('u', 0),
            'Pco': Variant('a(ubay)', []),
            'InitialEpsBearer': Variant('o', '/'),
            'InitialEpsBearerSettings': Variant('a{sv}', {})
        }
        self.UpdateRegistration()

    def UpdateRegistration(self):
        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            self.props['OperatorName'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
            self.props['OperatorCode'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value if "MobileNetworkCode" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
            if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unregisered":
                self.props['RegistrationState'] = Variant('u', 0)
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "registered":
                self.props['RegistrationState'] = Variant('u', 1)
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "searching":
                self.props['RegistrationState'] = Variant('u', 2)
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "denied":
                self.props['RegistrationState'] = Variant('u', 3)
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unknown":
                self.props['RegistrationState'] = Variant('u', 4)
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "roaming":
                self.props['RegistrationState'] = Variant('u', 5)
        self.emit_properties_changed({'RegistrationState': self.props['RegistrationState'].value})
        self.emit_properties_changed({'OperatorName': self.props['OperatorName'].value})
        self.emit_properties_changed({'OperatorCode': self.props['OperatorCode'].value})

    @dbus_property(access=PropertyAccess.READ)
    def Imei(self) -> 's':
        return self.props['Imei'].value

    @dbus_property(access=PropertyAccess.READ)
    def RegistrationState(self) -> 'u':
        return self.props['RegistrationState'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorCode(self) -> 's':
        return self.props['OperatorCode'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorName(self) -> 's':
        return self.props['OperatorName'].value

    @dbus_property(access=PropertyAccess.READ)
    def EnableFacilityLocks(self) -> 'u':
        return self.props['EnableFacilityLocks'].value

    @dbus_property(access=PropertyAccess.READ)
    def SubscriptionState(self) -> 'u':
        return self.props['SubscriptionState'].value

    @dbus_property(access=PropertyAccess.READ)
    def EpsUeModeOperation(self) -> 'u':
        return self.props['EpsUeModeOperation'].value

    @dbus_property(access=PropertyAccess.READ)
    def Pco(self) -> 'a(ubay)':
        return self.props['Pco'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearer(self) -> 'o':
        return self.props['InitialEpsBearer'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearerSettings(self) -> 'a{sv}':
        return self.props['InitialEpsBearerSettings'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.UpdateRegistration()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            self.ofono_interface_props[iface][name] = varval
            self.UpdateRegistration()
        return ch
