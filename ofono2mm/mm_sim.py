from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

class MMSimInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Sim')
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
                'Active': Variant('b', True),
                'SimIdentifier': Variant('s', ''),
                'IMSI': Variant('s', '0'),
                'Eid': Variant('s', ''),
                'OperatorIdentifier': Variant('s', '0'),
                'OperatorName': Variant('s', 'Some Operator'),
                'EmergencyNumbers': Variant('as', [])
            }

    def set_props(self):
        old_props = self.props

        if 'org.ofono.SimManager' in self.ofono_interface_props:
            if 'Present' in self.ofono_interface_props['org.ofono.SimManager']:
                if self.ofono_interface_props['org.ofono.SimManager']:
                    self.props['Active'] = Variant('b', True)
                else:
                    self.props['Active'] = Variant('b', False)
            else:
                self.props['Active'] = Variant('b', False)
            if 'CardIdentifier' in self.ofono_interface_props['org.ofono.SimManager']:
                self.props['SimIdentifier'] = Variant('s', self.ofono_interface_props['org.ofono.SimManager']['CardIdentifier'].value)
            else:
                self.props['SimIdentifier'] = Variant('s', '')
            if 'SubscriberIdentity' in self.ofono_interface_props['org.ofono.SimManager']:
                self.props['IMSI'] = Variant('s', self.ofono_interface_props['org.ofono.SimManager']['SubscriberIdentity'].value)
            else:
                self.props['IMSI'] = Variant('s', '')
        else:
            self.props['Active'] = Variant('b', False)
            self.props['SimIdentifier'] = Variant('s', '')
            self.props['IMSI'] = Variant('s', '')

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            self.props['OperatorName'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
            self.props['OperatorIdentifier'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value if "MobileNetworkCode" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
        else:
            self.props['OperatorName'] = Variant('s', '')
            self.props['OperatorIdentifier'] = Variant('s', '')

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @method()
    async def SendPin(self, pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_enter_pin('pin', pin)

    @method()
    async def SendPuk(self, puk: 's', pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_reset_pin('pin', puk, pin)

    @method()
    async def EnablePin(self, pin: 's', enabled: 'b'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            if enabled:
                await self.ofono_interfaces['org.ofono.SimManager'].call_lock_pin('pin', pin)
            else:
                await self.ofono_interfaces['org.ofono.SimManager'].call_unlock_pin('pin', pin)

    @method()
    async def ChangePin(self, old_pin: 's', new_pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_change_pin('pin', old_pin, new_pin)

    @dbus_property(access=PropertyAccess.READ)
    def Active(self) -> 'b':
        return self.props['Active'].value

    @dbus_property(access=PropertyAccess.READ)
    def SimIdentifier(self) -> 's':
        return self.props['SimIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def IMSI(self) -> 's':
        return self.props['IMSI'].value

    @dbus_property(access=PropertyAccess.READ)
    def Eid(self) -> 's':
        return self.props['Eid'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorIdentifier(self) -> 's':
        return self.props['OperatorIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorName(self) -> 's':
        return self.props['OperatorName'].value

    @dbus_property(access=PropertyAccess.READ)
    def EmergencyNumbers(self) -> 'as':
        return self.props['EmergencyNumbers'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_props()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            self.set_props()
        return ch

