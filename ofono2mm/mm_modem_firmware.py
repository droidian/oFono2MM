from dbus_next.service import (ServiceInterface, method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemFirmwareInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Firmware')
        self.mm_modem = mm_modem
        self.set_props()

    def set_props(self):
        hardware_revision = self.mm_modem.props.get('HardwareRevision', Variant('s', ''))

        self.props = {
            'UpdateSettings': Variant('(ua{sv})', [1, {
                'device-ids': Variant('as', ['OFONO-BINDER-PLUGIN']),
                'version': hardware_revision,
            }])
        }

    def emit_props_change(self):
        old_props = self.props.copy()
        self.set_props()

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @dbus_property(access=PropertyAccess.READ)
    def UpdateSettings(self) -> '(ua{sv})':
        return self.props['UpdateSettings'].value

    @method()
    async def List(self) -> 'saa{sv}':
        hardware_revision = self.mm_modem.props.get('HardwareRevision', Variant('s', ''))
        selected = hardware_revision.value

        installed_firmware = [
            {
                'image-type': Variant('u', 1),
                'unique-id': selected
            }
        ]

        return [selected, [installed_firmware]]

    @method()
    def Select(self, uniqueid: 's'):
        pass
