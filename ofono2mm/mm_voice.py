from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.mm_call import MMCallInterface

import time

call_i = 1

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

    async def init_calls(self):
        if 'org.ofono.VoiceCallManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.VoiceCallManager'].on_call_added(self.add_call)

        if 'org.ofono.VoiceCallManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.VoiceCallManager'].on_call_removed(self.remove_call)

    async def add_call(self, path, props):
        global call_i
        # TODO: init mm_call and set props then export the bus
        # for now we just want to know if a call has coming through or not
        self.CallAdded(path)
        call_i += 1

    async def remove_call(self, path):
        # TODO: delete and unexport the object. not needed for now
        self.CallDeleted(path)

        # print(f"call deleted: {path}")
        if 'org.ofono.ConnectionManager' in self.ofono_interfaces:
            contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts()
            self.context_names = []
            ctx_idx = 0
            chosen_apn = None
            chosen_ctx_path = None
            for ctx in contexts:
                name = ctx[1].get('Type', Variant('s', '')).value
                access_point_name = ctx[1].get('AccessPointName', Variant('s', '')).value
                if name.lower() == "internet":
                    ctx_idx += 1
                    if access_point_name:
                        self.context_names.append(access_point_name)
                        chosen_apn = access_point_name
                        chosen_ctx_path = ctx[0]

                if chosen_ctx_path:
                    # print(f'activate context on apn {chosen_apn}')
                    chosen_ctx_interface = self.ofono_client["ofono_context"][chosen_ctx_path]['org.ofono.ConnectionContext']
                    # on some carriers context does not get reactivated after a call automatically, lets do it ourselves just in case
                    time.sleep(2) # wait a bit for the call to end
                    try:
                        await chosen_ctx_interface.call_set_property("Active", Variant('b', True))
                    except Exception as e:
                        pass

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
        # print(f"call added: {path}")
        return path

    @signal()
    def CallDeleted(self, path) -> 'o':
        # print(f"call deleted: {path}")
        return path

    @dbus_property(access=PropertyAccess.READ)
    def Calls(self) -> 'ao':
        return self.props['Calls'].value

    @dbus_property(access=PropertyAccess.READ)
    def EmergencyOnly(self) -> 'b':
        return self.props['EmergencyOnly'].value
