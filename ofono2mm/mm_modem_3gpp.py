from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

class MMModem3gppInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_client, modem_name, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp')
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
            'Imei': Variant('s', ''),
            'RegistrationState': Variant('u', 0),
            'OperatorCode': Variant('s', ''),
            'OperatorName': Variant('s', ''),
            'EnableFacilityLocks': Variant('u', 0),
            'SubscriptionState': Variant('u', 0),
            'EpsUeModeOperation': Variant('u', 0),
            'Pco': Variant('a(ubay)', []),
            'InitialEpsBearer': Variant('o', '/'),
            'InitialEpsBearerSettings': Variant('a{sv}', {})
        }

    def set_props(self):
        old_props = self.props.copy()
        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            self.props['OperatorName'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
            self.props['OperatorCode'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value if "MobileNetworkCode" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
            if 'Status' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unregisered":
                    self.props['RegistrationState'] = Variant('u', 0)
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "registered":
                    self.props['RegistrationState'] = Variant('u', 1)
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "searching":
                    self.props['RegistrationState'] = Variant('u', 2)
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "denied":
                    self.props['RegistrationState'] = Variant('u', 3)
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unknown":
                    self.props['RegistrationState'] = Variant('u', 4)
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "roaming":
                    self.props['RegistrationState'] = Variant('u', 5)
            else:
                self.props['RegistrationState'] = Variant('u', 4)
        else:
            self.props['OperatorName'] = Variant('s', '')
            self.props['OperatorCode'] = Variant('s', '')
            self.props['RegistrationState'] = Variant('u', 4)

        self.props['Imei'] = Variant('s', self.ofono_props['Serial'].value if 'Serial' in self.ofono_props else '')
        self.props['EnableFacilityLocks'] = Variant('u', 0)

        changed_props = {}
        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                changed_props.update({ prop: self.props[prop].value })
        self.emit_properties_changed(changed_props)

    @method()
    async def Register(self, operator_id: 's'):
        if operator_id == "":
            if 'org.ofono.NetworkRegistration' in self.ofono_interfaces:
                try:
                    await self.ofono_interfaces['org.ofono.NetworkRegistration'].call_register()
                except DBusError:
                    pass
            return
        try:
            ofono_operator_interface = self.ofono_client["ofono_operator"][str(self.modem_name) + "/operator/" + str(operator_id)]['org.ofono.NetworkOperator']
            await ofono_operator_interface.call_register()
        except DBusError:
            return


    @method()
    async def Scan(self) -> 'aa{sv}':
        operators = []
        ofono_operators = await self.ofono_interfaces['org.ofono.NetworkRegistration'].call_scan()
        for ofono_operator in ofono_operators:
            mm_operator = {}
            if ofono_operator[1]['Status'].value == "unknown":
                mm_operator.update({'status': Variant('u', 0)})
            if ofono_operator[1]['Status'].value == "available":
                mm_operator.update({'status': Variant('u', 1)})
            if ofono_operator[1]['Status'].value == "current":
                mm_operator.update({'status': Variant('u', 2)})
            if ofono_operator[1]['Status'].value == "forbidden":
                mm_operator.update({'status': Variant('u', 3)})
            mm_operator.update({'operator-long': ofono_operator[1]['Name']})
            mm_operator.update({'operator-short': ofono_operator[1]['Name']})
            mm_operator.update({'operator-code': Variant('s', ofono_operator[1]['MobileCountryCode'].value + ofono_operator[1]['MobileNetworkCode'].value)})
            current_tech = 0
            for tech in ofono_operator[1]['Technologies'].value:
                if tech == "lte":
                    current_tech |= 1 << 14
                elif tech == "umts":
                    current_tech |= 1 << 5
                elif tech == "gsm":
                    current_tech |= 1 << 1
            mm_operator.update({'access-technology': Variant('u', current_tech)})
            operators.append(mm_operator)
        return operators

    @dbus_property(access=PropertyAccess.READ)
    def Imei(self) -> 's':
        return self.props['Imei'].value

    @dbus_property(access=PropertyAccess.READ)
    def RegistrationState(self) -> 'u':
        return self.props['RegistrationState'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorCode(self) -> 's':
        return self.props['OperatorCode'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorName(self) -> 's':
        return self.props['OperatorName'].value

    @dbus_property(access=PropertyAccess.READ)
    def EnableFacilityLocks(self) -> 'u':
        return self.props['EnableFacilityLocks'].value

    @dbus_property(access=PropertyAccess.READ)
    def SubscriptionState(self) -> 'u':
        return self.props['SubscriptionState'].value

    @dbus_property(access=PropertyAccess.READ)
    def EpsUeModeOperation(self) -> 'u':
        return self.props['EpsUeModeOperation'].value

    @dbus_property(access=PropertyAccess.READ)
    def Pco(self) -> 'a(ubay)':
        return self.props['Pco'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearer(self) -> 'o':
        return self.props['InitialEpsBearer'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearerSettings(self) -> 'a{sv}':
        return self.props['InitialEpsBearerSettings'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_props()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            self.set_props()
        return ch
