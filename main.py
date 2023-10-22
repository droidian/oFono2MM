#!/usr/bin/env python3
from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import DBusError, BusType

import asyncio

from ofono2mm import MMModemInterface, Ofono
from ofono2mm.utils import async_locked

has_bus = False

class MMInterface(ServiceInterface):
    def __init__(self, loop, bus, ofono_client):
        super().__init__('org.freedesktop.ModemManager1')
        self.loop = loop
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_manager_interface = self.ofono_client["ofono"]["/"]["org.ofono.Manager"]
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.14.10'

    @method()
    async def ScanDevices(self):
        await self.find_ofono_modems()

    @async_locked
    async def find_ofono_modems(self):
        global has_bus

        for mm_object in self.mm_modem_objects:
            self.bus.unexport(mm_object)

        self.mm_modem_objects = []
        self.mm_modem_intefaces = []

        self.ofono_modem_list = False
        while not self.ofono_modem_list:
            try:
                self.ofono_modem_list = [
                    x
                    for x in await self.ofono_manager_interface.call_get_modems()
                    if x[0].startswith("/ril_") # FIXME
                ]
            except DBusError:
                pass

        i = 0

        for modem in self.ofono_modem_list:
            mm_modem_interface = MMModemInterface(self.loop, i, self.bus, self.ofono_client, modem[0])
            ofono_modem_props = False
            while not ofono_modem_props:
                try:
                    ofono_modem_interface = self.ofono_client["ofono_modem"][modem[0]]['org.ofono.Modem']
                    ofono_modem_interface.on_property_changed(mm_modem_interface.ofono_changed)
                    ofono_modem_props = await ofono_modem_interface.call_get_properties()
                except DBusError:
                    pass
            mm_modem_interface.ofono_modem = ofono_modem_interface
            mm_modem_interface.ofono_props = ofono_modem_props
            await mm_modem_interface.init_ofono_interfaces()
            self.bus.export('/org/freedesktop/ModemManager1/Modem/' + str(i), mm_modem_interface)
            mm_modem_interface.set_props()
            await mm_modem_interface.init_mm_sim_interface()
            await mm_modem_interface.init_mm_3gpp_interface()
            await mm_modem_interface.init_mm_messaging_interface()
            await mm_modem_interface.init_mm_simple_interface()
            self.mm_modem_interfaces.append(mm_modem_interface)
            self.mm_modem_objects.append('/org/freedesktop/ModemManager1/Modem/' + str(i))
            i += 1

        if not has_bus and len(self.mm_modem_objects) != 0:
            await self.bus.request_name('org.freedesktop.ModemManager1')
            has_bus = True

    def ofono_modem_added(self, path, mprops):
       self.loop.create_task(self.find_ofono_modems())

    def ofono_modem_removed(self, path):
       self.loop.create_task(self.find_ofono_modems())

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
    ofono_client = Ofono(bus)
    ofono_manager_interface = False
    while not ofono_manager_interface:
        try:
            ofono_manager_interface = ofono_client["ofono"]["/"]["org.ofono.Manager"]
        except DBusError:
            pass
    
    loop = asyncio.get_running_loop()
    mm_manager_interface = MMInterface(loop, bus, ofono_client)
    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)
    await mm_manager_interface.find_ofono_modems()
    ofono_manager_interface.on_modem_added(mm_manager_interface.ofono_modem_added)
    ofono_manager_interface.on_modem_removed(mm_manager_interface.ofono_modem_removed)

    await bus.wait_for_disconnect()

asyncio.run(main())

