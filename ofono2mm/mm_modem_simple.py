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

        try:
            await self.mm_modem.bearers[bearer].doConnect()
        except Exception as e:
            pass

        return bearer

    @method()
    async def Disconnect(self, path: 'o'):
        if path == '/':
            for b in self.mm_modem.bearers:
                try:
                    await self.mm_modem.bearers[b].doDisconnect()
                except Exception as e:
                    pass
        if path in self.mm_modem.bearers:
            try:
                await self.mm_modem.bearers[path].doDisconnect()
            except Exception as e:
                pass

    @method()
    async def GetStatus(self) -> 'a{sv}':
        status_properties = {}

        status_properties["state"] = Variant("u", 9)
        status_properties["signal-quality"] = Variant("(ub)", (100, True))
        status_properties["current-bands"] = Variant("au", [0])
        status_properties["access-technologies"] = Variant("u", 19)
        status_properties["m3gpp-registration-state"] = Variant("u", 4)
        status_properties["m3gpp-operator-code"] = Variant("s", "")
        status_properties["m3gpp-operator-name"] = Variant("s", "")
        status_properties["cdma-cdma1x-registration-state"] = Variant("u", 0)
        status_properties["cdma-evdo-registration-state"] = Variant("u", 0)
        status_properties["cdma-sid"] = Variant("u", 0)
        status_properties["cdma-nid"] = Variant("u", 0)

        return status_properties
