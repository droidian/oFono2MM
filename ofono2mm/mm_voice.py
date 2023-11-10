from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.mm_call import MMCallInterface

class MMVoiceInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Voice')
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
                'Calls': Variant('ao', []),
                'EmergencyOnly': Variant('b', False),
            }

    @method()
    async def ListCalls(self) -> 'ao':
        try:
            result = await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_get_calls()

            if result and isinstance(result[0], (list, tuple)) and result[0]:
                ret = [result[0][0]]
            else:
                ret = []
        except IndexError:
            ret = []

        self.props['Calls'] = Variant('ao', ret)
        return ret

    @method()
    async def DeleteCall(self, path: 'o'):
        pass

    @method()
    async def CreateCall(self, properties: 'a{sv}') -> 'o':
        result = await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_dial(properties['Number'].value, 'disabled')
        return result

    @method()
    async def HoldAndAccept(self):
        result = await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_hold_and_answer()

    @method()
    async def HangupAndAccept(self):
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_release_and_answer()

    @method()
    async def HangupAll(self):
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_hangup_all()

    @method()
    async def Transfer(self):
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_transfer()

    @method()
    def CallWaitingSetup(self, enable: 'b'):
        pass

    @method()
    def CallWaitingQuery(self) -> 'b':
        pass

    @signal()
    def CallAdded(self, path) -> 's':
        return path

    @signal()
    def CallDeleted(self, path) -> 'o':
        return path

    @dbus_property(access=PropertyAccess.READ)
    def Calls(self) -> 'ao':
        return self.props['Calls'].value

    @dbus_property(access=PropertyAccess.READ)
    def EmergencyOnly(self) -> 'b':
        return self.props['EmergencyOnly'].value
