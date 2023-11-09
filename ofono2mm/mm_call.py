from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMCallInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Call')
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
                'State': Variant('i', 0),
                'StateReason': Variant('i', 0),
                'Direction': Variant('i', 0),
                'Number': Variant('s', ''),
                'Multiparty': Variant('b', False),
                'AudioPort': Variant('s', ''),
                'AudioFormat': Variant('a{sv}', [])
            }

    @method()
    def Start(self):
        pass

    @method()
    def Accept(self):
        pass

    @method()
    def Deflect(self, number: 's'):
        pass

    @method()
    def JoinMultiparty(self):
        pass

    @method()
    def LeaveMultiparty(self):
        pass

    @method()
    def Hangup(self):
        pass

    @method()
    def SendDtmf(self, dtmf: 's'):
        pass

    @signal()
    def DtmfReceived(self, dtmf) -> 's':
        return dtmf

    @signal()
    def StateChanged(self, old, new, reason) -> 'iiu':
        return [old, new, reason]

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'i':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def StateReason(self) -> 'i':
        return self.props['StateReason'].value

    @dbus_property(access=PropertyAccess.READ)
    def Direction(self) -> 'i':
        return self.props['Direction'].value

    @dbus_property(access=PropertyAccess.READ)
    def Number(self) -> 's':
        return self.props['Number'].value

    @dbus_property(access=PropertyAccess.READ)
    def Multiparty(self) -> 'b':
        return self.props['Multiparty'].value

    @dbus_property(access=PropertyAccess.READ)
    def AudioPort(self) -> 's':
        return self.props['AudioPort'].value

    @dbus_property(access=PropertyAccess.READ)
    def AudioFormat(self) -> 'a{sv}':
        return self.props['AudioFormat'].value
