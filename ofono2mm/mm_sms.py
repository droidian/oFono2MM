from dbus_next.service import (ServiceInterface,
                               dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMSmsInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Sms')
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
                "State": Variant('u', 0),
                "PduType": Variant('u', 0),
                "Number": Variant('s', ''),
                "Text": Variant('s', ''),
                "SMSC": Variant('s', ''),
                "Validity": Variant('(uv)', [0, Variant('u', 0)]),
                "Class": Variant('i', -1),
                "TeleserviceId": Variant('u', 0),
                "ServiceCategory": Variant('u', 0),
                "DeliveryReportRequest": Variant('b', False),
                "MessageReference": Variant('u', 0),
                "Timestamp": Variant('s', ''),
                "DischargeTimestamp": Variant('s', ''),
                "DeliveryState": Variant('u', 0),
                "Storage": Variant('u', 0)
            }

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'u':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def PduType(self) -> 'u':
        return self.props['PduType'].value

    @dbus_property(access=PropertyAccess.READ)
    def Number(self) -> 's':
        return self.props['Number'].value

    @dbus_property(access=PropertyAccess.READ)
    def Text(self) -> 's':
        return self.props['Text'].value

    @dbus_property(access=PropertyAccess.READ)
    def SMSC(self) -> 's':
        return self.props['SMSC'].value

    @dbus_property(access=PropertyAccess.READ)
    def Validity(self) -> '(uv)':
        return self.props['Validity'].value

    @dbus_property(access=PropertyAccess.READ)
    def Class(self) -> 'i':
        return self.props['Class'].value

    @dbus_property(access=PropertyAccess.READ)
    def TeleserviceId(self) -> 'u':
        return self.props['TeleserviceId'].value

    @dbus_property(access=PropertyAccess.READ)
    def ServiceCategory(self) -> 'u':
        return self.props['ServiceCategory'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeliveryReportRequest(self) -> 'b':
        return self.props['DeliveryReportRequest'].value

    @dbus_property(access=PropertyAccess.READ)
    def MessageReference(self) -> 'u':
        return self.props['MessageReference'].value

    @dbus_property(access=PropertyAccess.READ)
    def Timestamp(self) -> 's':
        return self.props['Timestamp'].value

    @dbus_property(access=PropertyAccess.READ)
    def DischargeTimestamp(self) -> 's':
        return self.props['DischargeTimestamp'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeliveryState(self) -> 'u':
        return self.props['DeliveryState'].value

    @dbus_property(access=PropertyAccess.READ)
    def Storage(self) -> 'u':
        return self.props['Storage'].value
