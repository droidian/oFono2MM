from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSarInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Sar')
        self.mm_modem = mm_modem
        self.props = {
            'State': Variant('b', False),
            'PowerLevel': Variant('u', 0)
        }

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'b':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def PowerLevel(self) -> 'u':
        return self.props['PowerLevel'].value

    @method()
    def Enable(self, enable: 'b'):
        self.props['State'] = Variant('b', enable)

    @method()
    def SetPowerLevel(self, level: 'u'):
        self.props['PowerLevel'] = Variant('u', level)
