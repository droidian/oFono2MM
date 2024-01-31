#!/usr/bin/env python3

from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError, BusType

import asyncio

from ofono2mm import MMModemInterface, Ofono, DBus
from ofono2mm.utils import async_locked

class MMInterface(ServiceInterface):
    def __init__(self, loop, bus):
        super().__init__('org.freedesktop.ModemManager1')
        self.loop = loop
        self.bus = bus
        self.ofono_client = Ofono(bus)
        self.dbus_client = DBus(bus)
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []
        self.loop.create_task(self.run_modem())

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.22.0'

    @method()
    async def ScanDevices(self):
        try:
            await self.find_ofono_modems()
        except:
            pass

    async def run_modem(self):
        mprops = {
            'Online': Variant('b', False),
            'Powered': Variant('b', True),
            'Lockdown': Variant('b', False),
            'Emergency': Variant('b', False),
            'Revision': Variant('s', '1'),
            'Serial': Variant('s', '1'),
            'SoftwareVersionNumber': Variant('s', '02'),
            'Interfaces': Variant('as', ['org.ofono.VoiceCallManager', 'org.ofono.SimManager', 'org.ofono.OemRaw', 'org.nemomobile.ofono.CellInfo', 'org.nemomobile.ofono.SimInfo']),
            'Features': Variant('as', ['sim']),
            'Type': Variant('s', 'hardware')
        }

        await self.export_new_modem("/ril_0", mprops)

    async def export_new_modem(self, path, mprops):
        self.i = 0
        mm_modem_interface = MMModemInterface(self.loop, self.i, self.bus, self.ofono_client, path)
        mm_modem_interface.ofono_props = mprops
        self.ofono_client["ofono_modem"][path]['org.ofono.Modem'].on_property_changed(mm_modem_interface.ofono_changed)
        await mm_modem_interface.init_ofono_interfaces()
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.i}', mm_modem_interface)
        mm_modem_interface.set_props()
        await mm_modem_interface.init_mm_sim_interface()
        await mm_modem_interface.init_mm_3gpp_interface()
        await mm_modem_interface.init_mm_3gpp_ussd_interface()
        await mm_modem_interface.init_mm_3gpp_profile_manager_interface()
        await mm_modem_interface.init_mm_messaging_interface()
        await mm_modem_interface.init_mm_simple_interface()
        await mm_modem_interface.init_mm_firmware_interface()
        await mm_modem_interface.init_mm_time_interface()
        await mm_modem_interface.init_mm_cdma_interface()
        await mm_modem_interface.init_mm_sar_interface()
        await mm_modem_interface.init_mm_oma_interface()
        await mm_modem_interface.init_mm_signal_interface()
        await mm_modem_interface.init_mm_location_interface()
        await mm_modem_interface.init_mm_voice_interface()
        self.mm_modem_interfaces.append(mm_modem_interface)
        self.mm_modem_objects.append(f'/org/freedesktop/ModemManager1/Modem/{self.i}')
        self.i += 1

    def ofono_modem_removed(self, path):
        for mm_object in self.mm_modem_objects:
            try:
                if mm_object.modem_name == path:
                    self.bus.unexport(mm_object)
            except Exception as e:
                pass

    @method()
    def SetLogging(self, level: 's'):
        pass

    @method()
    def ReportKernelEvent(self, properties: 'a{sv}'):
        pass

    @method()
    def InhibitDevice(self, uid: 's', inhibit: 'b'):
        pass

async def main():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    loop = asyncio.get_running_loop()
    mm_manager_interface = MMInterface(loop, bus)
    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)
    await bus.request_name('org.freedesktop.ModemManager1')

    await bus.wait_for_disconnect()

asyncio.run(main())
