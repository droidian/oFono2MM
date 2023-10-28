from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemCDMAInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.ModemCdma')
        self.mm_modem = mm_modem

        self.activation_state = 0
        self.meid = ""
        self.esn = ""
        self.sid = 0
        self.nid = 0
        self.cdma1x_registration_state = 0
        self.evdo_registration_state = 0

    @method()
    def Activate(self, carrier_code: 's'):
        pass

    @method()
    def ActivateManuel(self, properties: 'a{sv}') -> 'o':
        pass

    @dbus_property(access=PropertyAccess.READ)
    def ActivationState(self) -> 'u':
        return self.activation_state

    @dbus_property(access=PropertyAccess.READ)
    def Meid(self) -> 's':
        return self.meid

    @dbus_property(access=PropertyAccess.READ)
    def Esn(self) -> 's':
        return self.esn

    @dbus_property(access=PropertyAccess.READ)
    def Sid(self) -> 'u':
        return self.sid

    @dbus_property(access=PropertyAccess.READ)
    def Nid(self) -> 'u':
        return self.nid

    @dbus_property(access=PropertyAccess.READ)
    def Cdma1xRegistrationState(self) -> 'u':
        return self.cdma1x_registration_state

    @dbus_property(access=PropertyAccess.READ)
    def EvdoRegistrationState(self) -> 'u':
        return self.evdo_registration_state
