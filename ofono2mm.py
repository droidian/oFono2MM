#!/usr/bin/env python3
from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next.errors import DBusError
from dbus_next import Variant, DBusError, BusType

import asyncio

class MMInterface(ServiceInterface):
    def __init__(self):
        super().__init__('org.freedesktop.ModemManager1')

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.14.10'

    @method()
    def ScanDevices(self):
        pass

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
    def __init__(self, ofono_modem, ofono_props, ofono_sim, ofono_sim_props, ofono_netr, ofono_netr_props, ofono_radio, ofono_radio_props):
        super().__init__('org.freedesktop.ModemManager1.Modem')
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_sim = ofono_sim
        self.ofono_sim_props = ofono_sim_props
        self.ofono_netr = ofono_netr
        self.ofono_netr_props = ofono_netr_props
        self.ofono_radio = ofono_radio
        self.ofono_radio_props = ofono_radio_props
        self.props = {
                    'Sim': Variant('o', '/org/freedesktop/ModemManager1/SIMs/1'),
                    'SimSlots': Variant('ao', ['/org/freedesktop/ModemManager1/SIMs/1']),
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
        self.set_states()

    def set_states(self):
        old_state = self.props['State'].value
        if self.ofono_props['Powered'].value:
            if self.ofono_sim_props['Present'].value:
                if self.ofono_sim_props['PinRequired'].value == 'none':
                    self.props['UnlockRequired'] = Variant('u', 1)
                    if self.ofono_props['Online'].value and ("Status" in self.ofono_netr_props):
                        if self.ofono_netr_props['Status'].value == 'registered' or self.ofono_netr_props['Status'].value == 'roaming':
                            self.props['State'] = Variant('i', 8)
                            if 'Strength' in self.ofono_netr_props:
                                self.props['SignalQuality'] = Variant('(ub)', [self.ofono_netr_props['Strength'].value, True])
                        elif selfofono_netr_props['Status'].value == 'searching':
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

        if "Technology" in self.ofono_netr_props:
            current_tech = 0
            if self.ofono_netr_props["Technology"].value == "lte":
                current_tech |= 1 << 14
            elif self.ofono_netr_props["Technology"].value == "umts":
                current_tech |= 1 << 5
            elif self.ofono_netr_props["Technology"].value == "gsm":
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

    def ofono_sim_changed(self, name, varval):
        self.ofono_sim_props[name] = varval
        self.set_states()

    def ofono_netr_changed(self, name, varval):
        self.ofono_netr_props[name] = varval
        self.set_states()

    def ofono_radio_changed(self, name, varval):
        self.ofono_radio_props[name] = varval
        self.set_states()

class MMModem3gppInterface(ServiceInterface):
    def __init__(self, ofono_modem, ofono_props, ofono_sim, ofono_sim_props, ofono_netr, ofono_netr_props, ofono_radio, ofono_radio_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp')
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_sim = ofono_sim
        self.ofono_sim_props = ofono_sim_props
        self.ofono_netr = ofono_netr
        self.ofono_netr_props = ofono_netr_props
        self.ofono_radio = ofono_radio
        self.ofono_radio_props = ofono_radio_props
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
        self.props['OperatorName'] = Variant('s', self.ofono_netr_props['Name'].value if "Name" in self.ofono_netr_props else '')
        self.props['OperatorCode'] = Variant('s', self.ofono_netr_props['MobileNetworkCode'].value if "MobileNetworkCode" in self.ofono_netr_props else '')
        if self.ofono_netr_props['Status'].value == "unregisered":
            self.props['RegistrationState'] = Variant('u', 0)
        elif self.ofono_netr_props['Status'].value == "registered":
            self.props['RegistrationState'] = Variant('u', 1)
        elif self.ofono_netr_props['Status'].value == "searching":
            self.props['RegistrationState'] = Variant('u', 2)
        elif self.ofono_netr_props['Status'].value == "denied":
            self.props['RegistrationState'] = Variant('u', 3)
        elif self.ofono_netr_props['Status'].value == "unknown":
            self.props['RegistrationState'] = Variant('u', 4)
        elif self.ofono_netr_props['Status'].value == "roaming":
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

    def ofono_sim_changed(self, name, varval):
        self.ofono_sim_props[name] = varval
        self.UpdateRegistration()

    def ofono_netr_changed(self, name, varval):
        self.ofono_netr_props[name] = varval
        self.UpdateRegistration()

    def ofono_radio_changed(self, name, varval):
        self.ofono_radio_props[name] = varval
        self.UpdateRegistration()

class MMSimInterface(ServiceInterface):
    def __init__(self, ofono_modem, ofono_props, ofono_sim, ofono_sim_props, ofono_netr, ofono_netr_props, ofono_radio, ofono_radio_props):
        super().__init__('org.freedesktop.ModemManager1.Sim')
        self.ofono_modem = ofono_modem
        self.ofono_props = ofono_props
        self.ofono_sim = ofono_sim
        self.ofono_sim_props = ofono_sim_props
        self.ofono_netr = ofono_netr
        self.ofono_netr_props = ofono_netr_props
        self.ofono_radio = ofono_radio
        self.ofono_radio_props = ofono_radio_props
        self.props = {
                'Active': Variant('b', False),
                'SimIdentifier': Variant('s', ''),
                'IMSI': Variant('s', ''),
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

    def ofono_sim_changed(self, name, varval):
        self.ofono_sim_props[name] = varval

    def ofono_netr_changed(self, name, varval):
        self.ofono_netr_props[name] = varval

    def ofono_radio_changed(self, name, varval):
        self.ofono_radio_props[name] = varval

async def main():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    with open('/usr/lib/ofono2mm/ofono.xml', 'r') as f:
        ofono_introspection = f.read()
    ofono_proxy = bus.get_proxy_object('org.ofono', '/ril_0', ofono_introspection)

    ofono_modem_interface = ofono_proxy.get_interface('org.ofono.Modem')
    ofono_sim_interface = ofono_proxy.get_interface('org.ofono.SimManager')
    ofono_netr_interface = ofono_proxy.get_interface('org.ofono.NetworkRegistration')
    ofono_radio_interface = ofono_proxy.get_interface('org.ofono.RadioSettings')
    ofono_props = await ofono_modem_interface.call_get_properties()
    ofono_sim_props = await ofono_sim_interface.call_get_properties()
    try:
        ofono_netr_props = await ofono_netr_interface.call_get_properties()
    except(DBusError):
        ofono_netr_props = {}
    try:
        ofono_radio_props = await ofono_radio_interface.call_get_properties()
    except(DBusError):
        ofono_radio_propr = {}

    mm_interface = MMInterface()
    mm_modem_interface_1 = MMModemInterface(ofono_modem_interface, ofono_props, ofono_sim_interface, ofono_sim_props, ofono_netr_interface, ofono_netr_props, ofono_radio_interface, ofono_radio_props)
    mm_modem3gpp_interface_1 = MMModem3gppInterface(ofono_modem_interface, ofono_props, ofono_sim_interface, ofono_sim_props, ofono_netr_interface, ofono_netr_props, ofono_radio_interface, ofono_radio_props)
    mm_sim_interface_1 = MMSimInterface(ofono_modem_interface, ofono_props, ofono_sim_interface, ofono_sim_props, ofono_netr_interface, ofono_netr_props, ofono_radio_interface, ofono_radio_props)

    ofono_modem_interface.on_property_changed(mm_modem_interface_1.ofono_changed)
    ofono_sim_interface.on_property_changed(mm_modem_interface_1.ofono_sim_changed)
    ofono_netr_interface.on_property_changed(mm_modem_interface_1.ofono_netr_changed)
    ofono_radio_interface.on_property_changed(mm_modem_interface_1.ofono_radio_changed)

    ofono_modem_interface.on_property_changed(mm_modem3gpp_interface_1.ofono_changed)
    ofono_sim_interface.on_property_changed(mm_modem3gpp_interface_1.ofono_sim_changed)
    ofono_netr_interface.on_property_changed(mm_modem3gpp_interface_1.ofono_netr_changed)
    ofono_radio_interface.on_property_changed(mm_modem3gpp_interface_1.ofono_radio_changed)

    ofono_modem_interface.on_property_changed(mm_sim_interface_1.ofono_changed)
    ofono_sim_interface.on_property_changed(mm_sim_interface_1.ofono_sim_changed)
    ofono_netr_interface.on_property_changed(mm_sim_interface_1.ofono_netr_changed)
    ofono_radio_interface.on_property_changed(mm_sim_interface_1.ofono_radio_changed)

    bus.export('/org/freedesktop/ModemManager1', mm_interface)

    bus.export('/org/freedesktop/ModemManager1/Modems/1', mm_modem_interface_1)
    bus.export('/org/freedesktop/ModemManager1/Modems/1', mm_modem3gpp_interface_1)
    bus.export('/org/freedesktop/ModemManager1/SIMs/1', mm_sim_interface_1)

    bus.export('/org/freedesktop/ModemManager/Modems/1', mm_modem_interface_1)
    bus.export('/org/freedesktop/ModemManager/Modems/1', mm_modem3gpp_interface_1)
    bus.export('/org/freedesktop/ModemManager/SIMs/1', mm_sim_interface_1)

    await bus.request_name('org.freedesktop.ModemManager1')
    await bus.wait_for_disconnect()

asyncio.get_event_loop().run_until_complete(main())
