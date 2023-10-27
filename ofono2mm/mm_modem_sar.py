from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSarInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Sar')
        self.mm_modem = mm_modem
        self.set_props()

    def set_props(self):
        state_val = self.mm_modem.props.get('State', False)
        if not isinstance(state_val, bool):
            state_val = False

        power_level_val = self.mm_modem.props.get('PowerLevel', 0)
        if not isinstance(power_level_val, int):
            power_level_val = 0

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
        self.props['State'] = Variant('b', enable)
        self.emit_props_change()

    @method()
    def SetPowerLevel(self, level: 'u'):
        self.props['PowerLevel'] = Variant('u', level)
        self.emit_props_change()
