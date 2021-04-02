from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next.errors import DBusError
from dbus_next import Variant, DBusError, BusType

import asyncio
import time

from ofono2mm.mm_modem_3gpp import MMModem3gppInterface
from ofono2mm.mm_sim import MMSimInterface

class MMModemInterface(ServiceInterface):
    def __init__(self, loop, index, bus, ofono_proxy):
        super().__init__('org.freedesktop.ModemManager1.Modem')
        self.loop = loop
        self.index = index
        self.bus = bus
        self.ofono_proxy = ofono_proxy
        self.ofono_modem = None
        self.ofono_props = {}
        self.ofono_interfaces = {}
        self.ofono_interface_props = {}
        self.mm_modem3gpp_interface = False
        self.mm_sim_interface = False
        self.sim = Variant('o', '/org/freedesktop/ModemManager/SIMs/' + str(self.index))
        self.props = {
                    'Sim': Variant('o', '/'),
                    'SimSlots': Variant('ao', ['/org/freedesktop/ModemManager/SIMs/' + str(self.index)]),
                    'PrimarySimSlot': Variant('u', 0),
                    'Bearers': Variant('ao', []),
                    'SupportedCapabilities': Variant('au', [0]),
                    'CurrentCapabilities': Variant('u', 0),
                    'MaxBearers': Variant('u', 0),
                    'MaxActiveBearers': Variant('u', 0),
                    'Manufacturer': Variant('s', ""),
                    'Model': Variant('s', ""),
                    'Revision': Variant('s', ''),
                    'CarrierConfiguration': Variant('s', ''),
                    'CarrierConfigurationRevision': Variant('s', ''),
                    'HardwareRevision': Variant('s', ""),
                    'DeviceIdentifier': Variant('s', "ofono_" + str(self.index)),
                    'Device': Variant('s', ''),
                    'Drivers': Variant('as', []),
                    'Plugin': Variant('s', 'ofono2mm'),
                    'PrimaryPort': Variant('s', 'ofono_' + str(self.index)),
                    'Ports': Variant('a(su)', []),
                    'EquipmentIdentifier': Variant('s', ''),
                    'UnlockRequired': Variant('u', 0), 
                    'UnlockRetries': Variant('a{uu}', {}),
                    'State': Variant('i', -1),
                    'StateFailedReason': Variant('u', 0),
                    'AccessTechnologies': Variant('u', 0),
                    'SignalQuality': Variant('(ub)', [0, False]),
                    'OwnNumbers': Variant('as', []),
                    'PowerState': Variant('u', 1),
                    'SupportedModes': Variant('a(uu)', [[0, 0]]),
                    'CurrentModes': Variant('(uu)', [0, 0]),
                    'SupportedBands': Variant('au', []),
                    'CurrentBands': Variant('au', []),
                    'SupportedIpFamilies': Variant('u', 0)
                }

    async def init_ofono_interfaces(self):
        for iface in self.ofono_props['Interfaces'].value:
            await self.add_ofono_interface(iface)

    async def add_ofono_interface(self, iface):
        self.ofono_interfaces.update({
            iface: self.ofono_proxy.get_interface(iface)
        })
        try:
            self.ofono_interface_props.update({
                iface: await self.ofono_interfaces[iface].call_get_properties()
            })
            if self.mm_modem3gpp_interface:
                self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            if self.mm_sim_interface:
                self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.ofono_interfaces[iface].on_property_changed(self.ofono_interface_changed(iface))
        except DBusError:
            self.ofono_interface_props.update({
                iface: {}
            })
            if self.mm_modem3gpp_interface:
                self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            if self.mm_sim_interface:
                self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.ofono_interfaces[iface].on_property_changed(self.ofono_interface_changed(iface))
        except AttributeError:
            pass
        self.set_props()
        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.set_props()
        if self.mm_sim_interface:
            self.mm_sim_interface.set_props()

    async def remove_ofono_interface(self, iface):
        if iface in self.ofono_interfaces:
            self.ofono_interfaces.pop(iface)
        if iface in self.ofono_interface_props:
            self.ofono_interface_props.pop(iface)
        self.set_props()
        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.mm_modem3gpp_interface.set_props()
        if self.mm_sim_interface:
            self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.mm_sim_interface.set_props()

    async def init_mm_sim_interface(self):
        self.mm_sim_interface = MMSimInterface(self.index, self.bus, self.ofono_proxy, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export('/org/freedesktop/ModemManager/SIMs/' + str(self.index), self.mm_sim_interface)
        self.mm_sim_interface.set_props()

    async def init_mm_3gpp_interface(self):
        self.mm_modem3gpp_interface = MMModem3gppInterface(self.index, self.bus, self.ofono_proxy, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export('/org/freedesktop/ModemManager1/Modems/' + str(self.index), self.mm_modem3gpp_interface)
        self.mm_modem3gpp_interface.set_props()

    def set_props(self):
        old_props = self.props.copy()
        old_state = self.props['State'].value
        if self.ofono_props['Powered'].value and 'org.ofono.SimManager' in self.ofono_interface_props:
            if 'Present' in self.ofono_interface_props['org.ofono.SimManager']:
                if self.ofono_interface_props['org.ofono.SimManager']['Present'].value:
                    if self.ofono_interface_props['org.ofono.SimManager']['PinRequired'].value == 'none':
                        self.props['UnlockRequired'] = Variant('u', 1)
                        if self.ofono_props['Online'].value and 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
                            if ("Status" in self.ofono_interface_props['org.ofono.NetworkRegistration']):
                                if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'registered' or self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'roaming':
                                    self.props['State'] = Variant('i', 8)
                                    if 'Strength' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                                        self.props['SignalQuality'] = Variant('(ub)', [self.ofono_interface_props['org.ofono.NetworkRegistration']['Strength'].value, True])
                                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'searching':
                                    self.props['State'] = Variant('i', 7)
                                else:
                                    self.props['State'] = Variant('i', 6)
                            else:
                                self.props['State'] = Variant('i', 6)
                        else:
                            self.props['State'] = Variant('i', 3)
                    else:
                        self.props['UnlockRequired'] = Variant('u', 2)
                        self.props['State'] = Variant('i', 2)
                    self.props['Sim'] = self.sim
                else:
                    self.props['Sim'] = Variant('o', '/')
                    self.props['State'] = Variant('i', -1)
                    self.props['StateFailedReason'] = Variant('i', 2)
            else:
                self.props['State'] = Variant('i', -1)
                self.props['StateFailedReason'] = Variant('i', 2)
            self.props['PowerState'] = Variant('i', 3)
        else:
            self.props['State'] = Variant('i', 3)
            self.props['PowerState'] = Variant('i', 1)

        if 'org.ofono.SimManager' in self.ofono_interface_props:
            self.props['OwnNumbers'] = Variant('as', self.ofono_interface_props['org.ofono.SimManager']['SubscriberNumbers'].value if 'SubscriberNumbers' in self.ofono_interface_props['org.ofono.SimManager'] else [])
        else:
            self.props['OwnNumbers'] = Variant('as', [])

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props and self.props['State'].value == 8:
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
        else:
            self.props['AccessTechnologies'] = Variant('u', 0)
            self.props['SignalQuality'] = Variant('(ub)', [0, True])

        caps = 0
        modes = 0
        pref = 0
        if 'org.ofono.RadioSettings' in self.ofono_interface_props:
            if 'AvailableTechnologies' in self.ofono_interface_props['org.ofono.RadioSettings']:
                ofono_techs = self.ofono_interface_props['org.ofono.RadioSettings']['AvailableTechnologies'].value
                if 'gsm' in ofono_techs:
                    caps |= 4
                    modes |= 2
                if 'umts' in ofono_techs:
                    caps |= 4
                    modes |= 4
                if 'lte' in ofono_techs:
                    caps |= 8
                    modes |= 8
            if 'TechnologyPreference' in self.ofono_interface_props['org.ofono.RadioSettings']:
                ofono_pref =  self.ofono_interface_props['org.ofono.RadioSettings']['TechnologyPreference'].value
                if ofono_pref == 'lte':
                    pref = 8
                if ofono_pref == 'umts':
                    pref = 4
                if ofono_pref == 'gsm':
                    pref = 2
        self.props['CurrentCapabilities'] = Variant('u', caps)
        self.props['SupportedCapabilities'] = Variant('au', [caps])

        supported_modes = []
        if modes == 14:
            supported_modes.append([14, 8])
            supported_modes.append([6, 4])
            supported_modes.append([2, 2])
        if modes == 12:
            supported_modes.append([12, 8])
            supported_modes.append([4, 4])
        if modes == 10:
            supported_modes.append([10, 8])
            supported_modes.append([2, 2])
        if modes == 8:
            supported_modes.append([8, 8])
        if modes == 6:
            supported_modes.append([6, 4])
            supported_modes.append([2, 2])
        if modes == 4:
            supported_modes.append([4, 4])
        if modes == 2:
            supported_modes.append([2, 2])

        self.props['SupportedModes'] = Variant('a(uu)', supported_modes)
        for mode in supported_modes:
            if mode[1] == pref:
                self.props['CurrentModes'] = Variant('(uu)', [mode[0], pref])

        self.props['EquipmentIdentifier'] = Variant('s', self.ofono_props['Serial'].value if 'Serial' in self.ofono_props else '')
        self.props['HardwareRevision'] = Variant('s', self.ofono_props['Revision'].value if 'Revision' in self.ofono_props else '')
        self.props['Manufacturer'] = Variant('s', self.ofono_props['Manufacturer'].value if 'Manufacturer' in self.ofono_props else '')
        self.props['Model'] = Variant('s', self.ofono_props['Model'].value if 'Model' in self.ofono_props else '')

        if old_state != self.props['State'].value:
            self.StateChanged(old_state, self.props['State'].value, 0)

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

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
        await self.ofono_modem.call_set_property('Powered', Variant('b', state > 1))

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
        if name == "Interfaces":
            for iface in varval.value:
                if not (iface in self.ofono_interfaces):
                    self.loop.create_task(self.add_ofono_interface(iface))
            for iface in self.ofono_interfaces:
                if not (iface in varval.value):
                    self.loop.create_task(self.remove_ofono_interface(iface))
        self.set_props()
        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.ofono_changed(name, varval)
        if self.mm_sim_interface:
            self.mm_sim_interface.ofono_changed(name, varval)

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
                self.set_props()
                if self.mm_modem3gpp_interface:
                    self.mm_modem3gpp_interface.ofono_interface_changed(iface)(name, varval)
                if self.mm_sim_interface:
                    self.mm_sim_interface.ofono_interface_changed(iface)(name, varval)
        return ch
