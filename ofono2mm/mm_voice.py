from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMVoiceInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Voice')
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
                'Calls': Variant('ao', []),
                'EmergencyOnly': Variant('b', False),
            }

    @method()
    def ListCalls(self) -> 'ao':
        pass

    @method()
    def DeleteCall(self, path: 'o'):
        pass

    @method()
    def CreateCall(self, properties: 'a{sv}') -> 'o':
        pass

    @method()
    def HoldAndAccept(self):
        pass

    @method()
    def HangupAndAccept(self):
        pass

    @method()
    def HangupAll(self):
        pass

    @method()
    def Transfer(self):
        pass

    @method()
    def CallWaitingSetup(self, enable: 'b'):
        pass

    @method()
    def CallWaitingQuery(self) -> 'b':
        pass

    @signal()
    def CallAdded(self, path) -> 's':
        return path

    @signal()
    def CallDeleted(self, path) -> 'o':
        return path

    @dbus_property(access=PropertyAccess.READ)
    def Calls(self) -> 'ao':
        return self.props['Calls'].value

    @dbus_property(access=PropertyAccess.READ)
    def EmergencyOnly(self) -> 'b':
        return self.props['EmergencyOnly'].value
