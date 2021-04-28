from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant


class MMSimInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, modem_name, ofono_modem,
                 ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Sim')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
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
            sim_manager = self.ofono_interface_props['org.ofono.SimManager']
            self.props['Active'] = Variant('b', 'Present' in sim_manager)
            sim_identifier = (sim_manager['CardIdentifier'].value
                              if 'CardIdentifier' in sim_manager
                              else '')
            self.props['SimIdentifier'] = Variant('s', sim_identifier)
            identity = (sim_manager['SubscriberIdentity'].value
                        if 'SubscriberIdentity' in sim_manager
                        else '')
            self.props['IMSI'] = Variant('s', identity)
        else:
            self.props['Active'] = False
            self.props['SimIdentifier'] = Variant('s', '')
            self.props['IMSI'] = Variant('s', '')

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            prop = 'org.ofono.NetworkRegistration'
            network_registration = self.ofono_interface_props[prop]
            name = (network_registration['Name'].value
                    if 'Name' in network_registration
                    else '')
            self.props['OperatorName'] = Variant('s', name)
            code = (network_registration['MobileNetworkCode'].value
                    if 'MobileNetworkCode' in network_registration
                    else '')
            self.props['OperatorIdentifier'] = Variant('s', code)
        else:
            self.props['OperatorName'] = Variant('s', '')
            self.props['OperatorIdentifier'] = Variant('s', '')

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @method()
    async def SendPin(self, pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await (self.ofono_interfaces['org.ofono.SimManager']
                   .call_enter_pin('pin', pin))

    @method()
    async def SendPuk(self, puk: 's', pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await (self.ofono_interfaces['org.ofono.SimManager']
                   .call_reset_pin('pin', puk, pin))

    @method()
    async def EnablePin(self, pin: 's', enabled: 'b'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            if enabled:
                await (self.ofono_interfaces['org.ofono.SimManager']
                       .call_lock_pin('pin', pin))
            else:
                await (self.ofono_interfaces['org.ofono.SimManager']
                       .call_unlock_pin('pin', pin))

    @method()
    async def ChangePin(self, old_pin: 's', new_pin: 's'):
        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await (self.ofono_interfaces['org.ofono.SimManager']
                   .call_change_pin('pin', old_pin, new_pin))

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
