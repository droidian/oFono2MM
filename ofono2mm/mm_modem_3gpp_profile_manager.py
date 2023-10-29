from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError
import asyncio

class MMModem3gppProfileManagerInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp.ProfileManager')
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.ofono_modem = self.ofono_proxy['org.ofono.Modem']
        self.index_field = 'profile-id'
        self.context_names = []
        self.props = {}
        asyncio.create_task(self.attach_to_ofono_signals())
        asyncio.create_task(self.set_props())

    async def attach_to_ofono_signals(self):
        self.ofono_modem.on_property_changed(self.handle_properties_changed)

    async def handle_properties_changed(self, changed_properties, invalidated_properties):
        await self.set_props()

    async def set_props(self):
        await self.check_ofono_contexts()
        self.props['Contexts'] = Variant('as', self.context_names)
        self.emit_properties_changed({'Contexts': self.context_names})

    async def check_ofono_contexts(self):
        if not 'org.ofono.ConnectionManager' in self.ofono_interfaces:
            return []

        contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts()
        self.context_names = []

        for ctx in contexts:
            access_point_name = ctx[1].get('AccessPointName', Variant('s', '')).value
            if access_point_name:
                 self.context_names.append(access_point_name)

        return self.context_names

    @method()
    async def List(self) -> 'aa{sv}':
        return [{}]

    @method()
    def Set(self, requested_properties: 'a{sv}') -> 'a{sv}':
        pass

    @method()
    def Delete(self, properties: 'a{sv}'):
        pass

    @signal()
    def Updated(self):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def IndexField(self) -> 's':
        return self.index_field

    @dbus_property(access=PropertyAccess.READ)
    async def Contexts(self) -> 'as':
        await self.set_props()
        return self.props['Contexts'].value
