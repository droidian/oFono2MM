from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModem3gppUssdInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp.Ussd')
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.network_notification = ''
        self.network_request = ''

    @method()
    async def Initiate(self, command: 's') -> 's':
        result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_initiate(command)
        return result[1].value

    @method()
    async def Respond(self, response: 's') -> 's':
        result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_respond(response)
        return result

    @method()
    async def Cancel(self):
        try:
            await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_cancel()
        except Exception as e:
            pass

    @dbus_property(access=PropertyAccess.READ)
    async def State(self) -> 'u':
        result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_get_properties()
        result_str = result['State'].value

        if result_str == 'idle':
            ussd_state = 1
        elif result_str == "active":
            ussd_state = 2
        elif result_str == "user-response":
            ussd_state = 3
        else:
            ussd_state = 0

        self.ofono_interfaces['org.ofono.SupplementaryServices'].on_notification_received(self.save_notification_received)
        self.ofono_interfaces['org.ofono.SupplementaryServices'].on_request_received(self.save_request_received)

        return ussd_state

    def save_notification_received(self, message):
        self.network_notification = message

    @dbus_property(access=PropertyAccess.READ)
    def NetworkNotification(self) -> 's':
        return self.network_notification

    def save_request_received(self, message):
        self.network_request = message

    @dbus_property(access=PropertyAccess.READ)
    async def NetworkRequest(self) -> 's':
        return self.network_request
