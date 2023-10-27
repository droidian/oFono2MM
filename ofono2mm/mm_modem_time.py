from datetime import datetime
from dbus_next.service import (ServiceInterface, method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemTimeInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Time')
        self.mm_modem = mm_modem
        self.network_time = datetime.now().isoformat()
        self.network_timezone = {
            'offset': Variant('i', 0),
            'dst-offset': Variant('i', 0),
            'leap-seconds': Variant('i', 0)
        }

    @dbus_property(access=PropertyAccess.READ)
    def NetworkTimezone(self) -> 'a{sv}':
        return self.network_timezone

    @method()
    async def GetNetworkTime(self) -> 's':
        self.network_time = datetime.now().isoformat()
        return self.network_time

    @signal()
    def NetworkTimeChanged(self, time: 's') -> 's':
        self.network_time = time
        return time

    def update_network_time(self):
        self.network_time = datetime.now().isoformat()
        self.NetworkTimeChanged(self.network_time)

    def update_network_timezone(self, offset, dst_offset, leap_seconds):
        self.network_timezone = {
            'offset': Variant('i', offset),
            'dst-offset': Variant('i', dst_offset),
            'leap-seconds': Variant('i', leap_seconds)
        }
