from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSarInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Sar')
        self.mm_modem = mm_modem
        self.state = False
        self.power_level = 0
        self.set_props()

    def set_props(self):
        state_val = self.state
        power_level_val = self.power_level
        self.props = {
            'State': Variant('b', state_val),
            'PowerLevel': Variant('u', power_level_val)
        }

    def emit_props_change(self):
        old_props = self.props.copy()
        self.set_props()

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'b':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def PowerLevel(self) -> 'u':
        return self.props['PowerLevel'].value

    @method()
    def Enable(self, enable: 'b'):
        self.state = enable
        self.props['State'] = Variant('b', enable)
        self.emit_props_change()

    @method()
    def SetPowerLevel(self, level: 'u'):
        self.power_level = level
        self.props['PowerLevel'] = Variant('u', level)
        self.emit_props_change()
