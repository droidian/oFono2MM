#!/usr/bin/env python3
from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import DBusError, BusType

import asyncio

from ofono2mm import MMModemInterface

has_bus = False


class MMInterface(ServiceInterface):
    def __init__(self, loop, bus, ofono_manager_interface):
        super().__init__('org.freedesktop.ModemManager1')
        self.loop = loop
        self.bus = bus
        self.ofono_manager_interface = ofono_manager_interface
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.14.10'

    @method()
    async def ScanDevices(self):
        await self.find_ofono_modems()

    async def find_ofono_modems(self):
        global has_bus

        for mm_object in self.mm_modem_objects:
            self.bus.unexport(mm_object)

        self.mm_modem_objects = []
        self.mm_modem_intefaces = []

        self.ofono_modem_list = False
        while not self.ofono_modem_list:
            try:
                self.ofono_modem_list = await self.ofono_manager_interface \
                                                  .call_get_modems()
            except DBusError:
                pass

        with open('/usr/lib/ofono2mm/ofono_modem.xml', 'r') as f:
            ofono_modem_introspection = f.read()

        i = 0

        for modem in self.ofono_modem_list:
            ofono_proxy = self.bus.get_proxy_object('org.ofono', modem[0],
                                                    ofono_modem_introspection)
            mm_modem_interface = MMModemInterface(loop, i, self.bus,
                                                  ofono_proxy, modem[0])
            ofono_modem_props = False
            while not ofono_modem_props:
                try:
                    ofono_modem_interface = \
                        ofono_proxy.get_interface('org.ofono.Modem')
                    ofono_modem_interface \
                        .on_property_changed(mm_modem_interface.ofono_changed)
                    ofono_modem_props = \
                        await ofono_modem_interface.call_get_properties()
                except DBusError:
                    pass
            mm_modem_interface.ofono_modem = ofono_modem_interface
            mm_modem_interface.ofono_props = ofono_modem_props
            await mm_modem_interface.init_ofono_interfaces()
            mm_modem_path = f"/org/freedesktop/ModemManager1/Modem/{i}"
            self.bus.export(mm_modem_path, mm_modem_interface)
            mm_modem_interface.set_props()
            await mm_modem_interface.init_mm_sim_interface()
            await mm_modem_interface.init_mm_3gpp_interface()
            await mm_modem_interface.init_mm_messaging_interface()
            self.mm_modem_interfaces.append(mm_modem_interface)
            self.mm_modem_objects.append(mm_modem_path)
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


async def main(loop):
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    with open('/usr/lib/ofono2mm/ofono.xml', 'r') as f:
        ofono_introspection = f.read()
    ofono_manager_interface = False
    while not ofono_manager_interface:
        try:
            ofono_proxy = bus.get_proxy_object('org.ofono', '/',
                                               ofono_introspection)
            ofono_manager_interface = \
                ofono_proxy.get_interface('org.ofono.Manager')
        except DBusError:
            pass

    mm_manager_interface = MMInterface(loop, bus, ofono_manager_interface)
    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)
    await mm_manager_interface.find_ofono_modems()
    ofono_manager_interface \
        .on_modem_added(mm_manager_interface.ofono_modem_added)
    ofono_manager_interface \
        .on_modem_removed(mm_manager_interface.ofono_modem_removed)

    await bus.wait_for_disconnect()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
