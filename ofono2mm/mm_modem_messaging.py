from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.mm_sms import MMSmsInterface

message_i = 1

class MMModemMessagingInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Messaging')
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
            'Messages': Variant('ao', []),
            'SupportedStorages': Variant('au', []),
            'DefaultStorage': Variant('u', 0)
        }

    def set_props(self):
        old_props = self.props

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    async def init_messages(self):
        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.MessageManager'].on_incoming_message(self.add_incoming_message)

    def add_incoming_message(self, msg, props):
        global message_i
        mm_sms_interface = MMSmsInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        mm_sms_interface.props.update({
            'State': Variant('u', 3),
            'PduType': Variant('u', 1),
            'Number': props['Sender'],
            'Text': Variant('s', msg),
            'Timestamp': props['SentTime']
        })
        self.bus.export('/org/freedesktop/ModemManager1/SMS/' + str(message_i), mm_sms_interface)
        self.props['Messages'].value.append('/org/freedesktop/ModemManager1/SMS/' + str(message_i))
        self.emit_properties_changed({'Messages': self.props['Messages'].value})
        self.Added('/org/freedesktop/ModemManager1/SMS/' + str(message_i), True)
        message_i += 1

    @method()
    async def List(self) -> 'ao':
        return self.props['Messages'].value

    @method()
    async def Delete(self, path: 'o'):
        if path in self.props['Messages'].value:
            self.props['Messages'].value.remove(path)
            self.bus.unexport(path)
            self.emit_properties_changed({'Messages': self.props['Messages'].value})
            self.Deleted(path)

    @method()
    async def Create(self, properties: 'a{sv}') -> 'o':
        global message_i
        if 'number' not in properties or 'text' not in properties:
            return
        mm_sms_interface = MMSmsInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        mm_sms_interface.props.update({
            'Text': properties['text'],
            'Number': properties['number'],
            'DeliveryReportRequest': properties['delivery-report-request'] if 'delivery-report-request' in properties else Variant('b', False)
        })
        self.bus.export('/org/freedesktop/ModemManager1/SMS/' + str(message_i), mm_sms_interface)
        self.props['Messages'].value.append('/org/freedesktop/ModemManager1/SMS/' + str(message_i))
        self.emit_properties_changed({'Messages': self.props['Messages'].value})
        self.Added('/org/freedesktop/ModemManager1/SMS/' + str(message_i), True)
        message_i += 1
        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            ofono_sms_path = await self.ofono_interfaces['org.ofono.MessageManager'].call_send_message(properties['number'].value, properties['text'].value)

    @signal()
    def Added(self, path, received) -> 'ob':
        return [path, received]

    @signal()
    def Deleted(self, path) -> 'o':
        return path

    @dbus_property(access=PropertyAccess.READ)
    def Messages(self) -> 'ao':
        return self.props['Messages'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedStorages(self) -> 'au':
        return self.props['SupportedStorages'].value

    @dbus_property(access=PropertyAccess.READ)
    def DefaultStorage(self) -> 'u':
        return self.props['DefaultStorage'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_props()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            self.set_props()
        return ch
