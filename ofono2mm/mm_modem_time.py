from datetime import datetime, timedelta, timezone
from dbus_next.service import (ServiceInterface, method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemTimeInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Time')
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.ofono_modem = self.ofono_proxy['org.ofono.Modem']
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
        if 'org.ofono.NetworkTime' in self.ofono_interfaces:
            ofono_interface = self.ofono_client["ofono_modem"][self.modem_name]['org.ofono.NetworkTime']
            output = await ofono_interface.call_get_network_time()

            if 'UTC' in output:
                utc_time = output['UTC'].value
                network_time = datetime.fromtimestamp(utc_time, tz=timezone.utc)
                self.network_time = network_time.isoformat()

                timezone_offset = output['Timezone'].value // 60
                dst_offset = output['DST'].value // 60

                self.update_network_timezone(timezone_offset, dst_offset, 0)
            else:
                self.network_time = datetime.now().isoformat()
        else:
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

        self.NetworkTimeChanged(self.network_time)
