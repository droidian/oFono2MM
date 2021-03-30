#!/usr/bin/env python3
from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next.errors import DBusError
from dbus_next import Variant, DBusError, BusType

import asyncio

class MMInterface(ServiceInterface):
    def __init__(self, bus, ofono_manager_interface):
        super().__init__('org.freedesktop.ModemManager1')
        self.bus = bus
        self.ofono_manager_interface = ofono_manager_interface
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.14.10'

    @method()
    async def ScanDevices(self):
        await self.find_ofono_modems()

    async def find_ofono_modems(self):
        for mm_object in self.mm_modem_objects:
            self.bus.unexport(mm_object)

        self.ofono_modem_list = await self.ofono_manager_interface.call_get_modems()

        with open('/usr/lib/ofono2mm/ofono_modem.xml', 'r') as f:
            ofono_modem_introspection = f.read()

        i = 1

        for modem in self.ofono_modem_list:
            ofono_proxy = self.bus.get_proxy_object('org.ofono', modem[0], ofono_modem_introspection)
            ofono_modem_interface = ofono_proxy.get_interface('org.ofono.Modem')
            ofono_modem_props = await ofono_modem_interface.call_get_properties()
            mm_modem_interface = MMModemInterface(i, self.bus, ofono_proxy, ofono_modem_interface, ofono_modem_props)
            ofono_modem_interface.on_property_changed(mm_modem_interface.ofono_changed)
            await mm_modem_interface.init_ofono_interfaces()
            await mm_modem_interface.init_mm_interfaces()
            mm_modem_interface.set_states()
            self.bus.export('/org/freedesktop/ModemManager1/Modems/' + str(i), mm_modem_interface)
            self.bus.export('/org/freedesktop/ModemManager/Modems/' + str(i), mm_modem_interface)
            self.mm_modem_interfaces.append(mm_modem_interface)
            self.mm_modem_objects.append('/org/freedesktop/ModemManager/Modems/' + str(i))
            self.mm_modem_objects.append('/org/freedesktop/ModemManager1/Modems/' + str(i))
            i += 1

    @method()
    def SetLogging(self, level: 's'):
        pass

    @method()
    def ReportKernelEvent(self, properties: 'a{sv}'):
        pass

    @method()
    def InhibitDevice(self, uid: 's', inhibit: 'b'):
        pass

class MMModemInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, ofono_modem, ofono_props):
        super().__init__('org.freedesktop.ModemManager1.Modem')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = {}
        self.ofono_interface_props = {}
        self.props = {
                    'Sim': Variant('o', '/org/freedesktop/ModemManager1/SIMs/' + str(self.index)),
                    'SimSlots': Variant('ao', ['/org/freedesktop/ModemManager1/SIMs/' + str(self.index)]),
                    'PrimarySimSlot': Variant('u', 0),
                    'Bearers': Variant('ao', []),
                    'SupportedCapabilities': Variant('au', [0, 4]),
                    'CurrentCapabilities': Variant('u', 4),
                    'MaxBearers': Variant('u', 0),
                    'MaxActiveBearers': Variant('u', 0),
                    'Manufacturer': Variant('s', ofono_props['Manufacturer'].value if 'Manufacturer' in ofono_props else "Unknown"),
                    'Model': Variant('s', ofono_props['Model'].value if 'Model' in ofono_props else "Unknown"),
                    'Revision': Variant('s', '1.0'),
                    'CarrierConfiguration': Variant('s', ''),
                    'CarrierConfigurationRevision': Variant('s', '1.0'),
                    'HardwareRevision': Variant('s', ofono_props['Revision'].value if 'Revision' in ofono_props else "Unknown"),
                    'DeviceIdentifier': Variant('s', 'ril_0'),
                    'Device': Variant('s', ''),
                    'Drivers': Variant('as', []),
                    'Plugin': Variant('s', 'ofono2mm'),
                    'PrimaryPort': Variant('s', ''),
                    'Ports': Variant('a(su)', []),
                    'EquipmentIdentifier': Variant('s', ofono_props['Serial'].value),
                    'UnlockRequired': Variant('u', 0), 
                    'UnlockRetries': Variant('a{uu}', {}),
                    'State': Variant('i', -1),
                    'StateFailedReason': Variant('u', 0),
                    'AccessTechnologies': Variant('u', 0),
                    'SignalQuality': Variant('(ub)', [0, True]),
                    'OwnNumbers': Variant('as', []),
                    'PowerState': Variant('u', 3 if ofono_props['Powered'].value else 1),
                    'SupportedModes': Variant('a(uu)', [[0, 0]]),
                    'CurrentModes': Variant('(uu)', [0, 0]),
                    'SupportedBands': Variant('au', []),
                    'CurrentBands': Variant('au', []),
                    'SupportedIpFamilies': Variant('u', 0)
                }

    async def init_ofono_interfaces(self):
        for iface in self.ofono_props['Interfaces'].value:
            self.ofono_interfaces.update({
                iface: self.ofono_proxy.get_interface(iface)
            })
            try:
                self.ofono_interface_props.update({
                    iface: await self.ofono_interfaces[iface].call_get_properties()
                })
                self.ofono_interfaces[iface].on_property_changed(self.ofono_interface_changed(iface))
            except AttributeError:
                self.ofono_interface_props.update({
                    iface: {}
                })

    async def init_mm_interfaces(self):
        self.mm_modem3gpp_interface = MMModem3gppInterface(self.index, self.bus, self.ofono_proxy, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.ofono_modem.on_property_changed(self.mm_modem3gpp_interface.ofono_changed)
        for iface in self.ofono_interfaces:
            try:
                self.ofono_interfaces[iface].on_property_changed(self.mm_modem3gpp_interface.ofono_interface_changed(iface))
            except AttributeError:
                pass
        self.bus.export('/org/freedesktop/ModemManager1/Modems/' + str(self.index), self.mm_modem3gpp_interface)
        self.bus.export('/org/freedesktop/ModemManager/Modems/' + str(self.index), self.mm_modem3gpp_interface)

        self.mm_sim_interface = MMSimInterface(self.index, self.bus, self.ofono_proxy, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.ofono_modem.on_property_changed(self.mm_sim_interface.ofono_changed)
        for iface in self.ofono_interfaces:
            try:
                self.ofono_interfaces[iface].on_property_changed(self.mm_sim_interface.ofono_interface_changed(iface))
            except AttributeError:
                pass
        self.bus.export('/org/freedesktop/ModemManager1/SIMs/' + str(self.index), self.mm_sim_interface)
        self.bus.export('/org/freedesktop/ModemManager/SIMs/' + str(self.index), self.mm_sim_interface)

    def set_states(self):
        old_state = self.props['State'].value
        if self.ofono_props['Powered'].value:
            if self.ofono_interface_props['org.ofono.SimManager']['Present'].value:
                if self.ofono_interface_props['org.ofono.SimManager']['PinRequired'].value == 'none':
                    self.props['UnlockRequired'] = Variant('u', 1)
                    if self.ofono_props['Online'].value and ("Status" in self.ofono_interface_props['org.ofono.NetworkRegistration']):
                        if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'registered' or self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'roaming':
                            self.props['State'] = Variant('i', 8)
                            if 'Strength' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                                self.props['SignalQuality'] = Variant('(ub)', [self.ofono_interface_props['org.ofono.NetworkRegistration']['Strength'].value, True])
                        elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'searching':
                            self.props['State'] = Variant('i', 7)
                        else:
                            self.props['State'] = Variant('i', 6)
                    else:
                        self.props['State'] = Variant('i', 3)
                else:
                    self.props['UnlockRequired'] = Variant('u', 2)
                    self.props['State'] = Variant('i', 2)
            else:
                self.props['StateFailedReason'] = Variant('i', 2)
        else:
            self.props['State'] = Variant('i', 3)

        if "Technology" in self.ofono_interface_props['org.ofono.NetworkRegistration']:
            current_tech = 0
            if self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "lte":
                current_tech |= 1 << 14
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "umts":
                current_tech |= 1 << 5
            elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "gsm":
                current_tech |= 1 << 1
            self.props['AccessTechnologies'] = Variant('u', current_tech)
        else:
            self.props['AccessTechnologies'] = Variant('u', 0)

        self.emit_properties_changed({'AccessTechnologies': self.props['AccessTechnologies'].value})
        self.emit_properties_changed({'State': self.props['State'].value})
        self.emit_properties_changed({'PowerState': self.props['PowerState'].value})
        self.emit_properties_changed({'UnlockRequired': self.props['UnlockRequired'].value})
        self.emit_properties_changed({'SignalQuality': self.props['SignalQuality'].value})
        self.StateChanged(old_state, self.props['State'].value, 0)

    @method()
    async def Enable(self, enable: 'b'):
        await self.ofono_modem.call_set_property('Online', Variant('b', enable))
    
    @method()
    def ListBearers(self) -> 'ao':
        return self.props['Bearers'].value

    @method()
    def CreateBearer(self, properties: 'a{sv}') -> 'o':
        return '/'

    @method()
    def DeleteBearer(self, bearer: 'o'):
        pass #TODO: Do delete it!

    @method()
    async def Reset(self):
        await self.ofono_modem.call_set_property('Powered', Variant('b', False))
        await self.ofono_modem.call_set_property('Powered', Variant('b', True))

    @method()
    def FactoryReset(self, code: 's'):
        pass #TODO: Do reset the modem!

    @method()
    async def SetPowerState(self, state: 'u'):
        await self.ofono_modem.call_set_property('Powered', Variant('b', state == 3))

    @method()
    def SetCurrentCapabilities(self, capabilities: 'u'):
        pass #TODO: Do set them!

    @method()
    def SetCurrentModes(self, modes: '(uu)'):
        pass #TODO: Do set them!

    @method()
    def SetCurrentBands(self, bands: 'au'):
        pass #TODO: Do set them!

    @method()
    def SetPrimarySimSlot(self, sim_slot: 'u'):
        pass #TODO: Do set it!

    @method()
    def Command(self, cmd: 's', timeout: 'u') -> 's':
        return ''

    @signal()
    def StateChanged(self, old, new, reason) -> 'iiu':
        return [old, new, reason]

    @dbus_property(access=PropertyAccess.READ)
    def Sim(self) -> 'o':
        return self.props['Sim'].value

    @dbus_property(access=PropertyAccess.READ)
    def SimSlots(self) -> 'ao':
        return self.props['SimSlots'].value

    @dbus_property(access=PropertyAccess.READ)
    def PrimarySimSlot(self) -> 'u':
        return self.props['PrimarySimSlot'].value

    @dbus_property(access=PropertyAccess.READ)
    def Bearers(self) -> 'ao':
        return self.props['Bearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedCapabilities(self) -> 'au':
        return self.props['SupportedCapabilities'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentCapabilities(self) -> 'u':
        return self.props['CurrentCapabilities'].value

    @dbus_property(access=PropertyAccess.READ)
    def MaxBearers(self) -> 'u':
        return self.props['MaxBearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def MaxActiveBearers(self) -> 'u':
        return self.props['MaxActiveBearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def Manufacturer(self) -> 's':
        return self.props['Manufacturer'].value

    @dbus_property(access=PropertyAccess.READ)
    def Model(self) -> 's':
        return self.props['Model'].value

    @dbus_property(access=PropertyAccess.READ)
    def Revision(self) -> 's':
        return self.props['Revision'].value

    @dbus_property(access=PropertyAccess.READ)
    def HardwareRevision(self) -> 's':
        return self.props['HardwareRevision'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeviceIdentifier(self) -> 's':
        return self.props['DeviceIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def Device(self) -> 's':
        return self.props['Device'].value

    @dbus_property(access=PropertyAccess.READ)
    def Drivers(self) -> 'as':
        return self.props['Drivers'].value

    @dbus_property(access=PropertyAccess.READ)
    def Plugin(self) -> 's':
        return self.props['Plugin'].value

    @dbus_property(access=PropertyAccess.READ)
    def PrimaryPort(self) -> 's':
        return self.props['PrimaryPort'].value

    @dbus_property(access=PropertyAccess.READ)
    def Ports(self) -> 'a(su)':
        return self.props['Ports'].value

    @dbus_property(access=PropertyAccess.READ)
    def EquipmentIdentifier(self) -> 's':
        return self.props['EquipmentIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def UnlockRequired(self) -> 'u':
        return self.props['UnlockRequired'].value

    @dbus_property(access=PropertyAccess.READ)
    def UnlockRetries(self) -> 'a{uu}':
        return self.props['UnlockRetries'].value

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'i':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def StateFailedReason(self) -> 'u':
        return self.props['StateFailedReason'].value

    @dbus_property(access=PropertyAccess.READ)
    def AccessTechnologies(self) -> 'u':
        return self.props['AccessTechnologies'].value

    @dbus_property(access=PropertyAccess.READ)
    def SignalQuality(self) -> '(ub)':
        return self.props['SignalQuality'].value

    @dbus_property(access=PropertyAccess.READ)
    def OwnNumbers(self) -> 'as':
        return self.props['OwnNumbers'].value

    @dbus_property(access=PropertyAccess.READ)
    def PowerState(self) -> 'u':
        return self.props['PowerState'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedModes(self) -> 'a(uu)':
        return self.props['SupportedModes'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentModes(self) -> '(uu)':
        return self.props['CurrentModes'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedBands(self) -> 'au':
        return self.props['SupportedBands'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentBands(self) -> 'au':
        return self.props['CurrentBands'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedIpFamilies(self) -> 'u':
        return self.props['SupportedIpFamilies'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_states()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            self.ofono_interface_props[iface][name] = varval
            self.set_states()
        return ch

class MMModem3gppInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
            'Imei': Variant('s', ofono_props['Serial'].value),
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
        self.UpdateRegistration()

    def UpdateRegistration(self):
        self.props['OperatorName'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
        self.props['OperatorCode'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value if "MobileNetworkCode" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')
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
        self.emit_properties_changed({'RegistrationState': self.props['RegistrationState'].value})
        self.emit_properties_changed({'OperatorName': self.props['OperatorName'].value})
        self.emit_properties_changed({'OperatorCode': self.props['OperatorCode'].value})

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
        self.UpdateRegistration()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            self.ofono_interface_props[iface][name] = varval
            self.UpdateRegistration()
        return ch

class MMSimInterface(ServiceInterface):
    def __init__(self, index, bus, ofono_proxy, ofono_modem, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Sim')
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
                'Active': Variant('b', False),
                'SimIdentifier': Variant('s', ''),
                'IMSI': Variant('s', '0'),
                'Eid': Variant('s', ''),
                'OperatorIdentifier': Variant('s', ''),
                'OperatorName': Variant('s', ''),
                'EmergencyNumbers': Variant('as', [])
            }

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

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            self.ofono_interface_props[iface][name] = varval
        return ch

async def main():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    with open('/usr/lib/ofono2mm/ofono.xml', 'r') as f:
        ofono_introspection = f.read()
    ofono_proxy = bus.get_proxy_object('org.ofono', '/', ofono_introspection)

    ofono_manager_interface = ofono_proxy.get_interface('org.ofono.Manager')

    mm_manager_interface = MMInterface(bus, ofono_manager_interface)
    await mm_manager_interface.find_ofono_modems()

    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)

    await bus.request_name('org.freedesktop.ModemManager1')
    await bus.wait_for_disconnect()

asyncio.get_event_loop().run_until_complete(main())
