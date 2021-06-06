from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSimpleInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Simple')
        self.mm_modem = mm_modem

    @method()
    async def Connect(self, properties: 'a{sv}') -> 'o':
        for b in self.mm_modem.bearers:
            if self.mm_modem.bearers[b].props['Properties'].value['apn'] == properties['apn']:
                await self.mm_modem.bearers[b].add_auth_ofono(properties['username'].value if 'username' in properties else '', 
                                                                properties['password'].value if 'password' in properties else '')
                self.mm_modem.bearers[b].props['Properties'] = Variant('a{sv}', properties)
                await self.mm_modem.bearers[b].doConnect()
                return b
        bearer = await self.mm_modem.doCreateBearer(properties)
        await self.mm_modem.bearers[bearer].doConnect()
        return bearer

    @method()
    async def Disconnect(self, path: 'o'):
        if path == '/':
            for b in self.mm_modem.bearers:
                await self.mm_modem.bearers[b].doDisconnect()
        if path in self.mm_modem.bearers:
            await self.mm_modem.bearers[path].doDisconnect()
