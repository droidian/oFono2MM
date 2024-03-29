from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSignalInterface(ServiceInterface):
    def __init__(self, mm_modem, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Signal')
        self.mm_modem = mm_modem
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
            'Rate': Variant('u', 0),
            'RssiThreshold': Variant('u', 0),
            'ErrorRateThreshold': Variant('b', False),
            'Cdma': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'ecio': Variant('d', 0),
                'error-rate': Variant('d', 0)
             }),
            'Evdo': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'ecio': Variant('d', 0),
                'sinr': Variant('d', 0),
                'io': Variant('d', 0),
                'error-rate': Variant('d', 0)
             }),
            'Gsm': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Umts': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'rscp': Variant('d', 0),
                'ecio': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Lte': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'rsrq': Variant('d', 0),
                'rsrp': Variant('d', 0),
                'snr': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Nr5g': Variant('a{sv}', {
                'rsrq': Variant('d', 0),
                'rsrp': Variant('d', 0),
                'snr': Variant('d', 0),
                'error-rate': Variant('d', 0)
            })
        }

    async def set_props(self):
        if 'org.ofono.NetworkMonitor' in self.ofono_interface_props:
            self.props['Cdma'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Evdo'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Gsm'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Umts'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Lte'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Cdma'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Evdo'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Gsm'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Umts'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Lte'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Lte'].value['rsrq'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['rsrq'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Lte'].value['rsrp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['rsrp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Umts'].value['rscp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalCodePower'].value if "ReceivedSignalCodePower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
        else:
            self.props['Cdma'].value['rssi'] = Variant('d', 0)
            self.props['Evdo'].value['rssi'] = Variant('d', 0)
            self.props['Gsm'].value['rssi'] = Variant('d', 0)
            self.props['Umts'].value['rssi'] = Variant('d', 0)
            self.props['Lte'].value['rssi'] = Variant('d', 0)

            self.props['Cdma'].value['error-rate'] = Variant('d', 0)
            self.props['Evdo'].value['error-rate'] = Variant('d', 0)
            self.props['Gsm'].value['error-rate'] = Variant('d', 0)
            self.props['Umts'].value['error-rate'] = Variant('d', 0)
            self.props['Lte'].value['error-rate'] = Variant('d', 0)
            self.props['Nr5g'].value['error-rate'] = Variant('d', 0)

            self.props['Lte'].value['rsrq'] = Variant('d', 0)
            self.props['Nr5g'].value['rsrq'] = Variant('d', 0)

            self.props['Lte'].value['rsrp'] = Variant('d', 0)
            self.props['Nr5g'].value['rsrp'] = Variant('d', 0)

            self.props['Umts'].value['rscp'] = Variant('d', 0)

    @method()
    async def Setup(self, rate: 'u'):
        try:
            await self.set_props()
        except Exception as e:
            pass

        self.props['Rate'] = Variant('u', rate)

    @method()
    def SetupThresholds(self, settings: 'a{sv}'):
        self.props['RssiThreshold'] = Variant('u', settings.get('rssi-threshold', Variant('u', 0)).value)
        self.props['ErrorRateThreshold'] = Variant('b', settings.get('error-rate-threshold', Variant('b', False)).value)

    @dbus_property(access=PropertyAccess.READ)
    def Rate(self) -> 'u':
        return self.props['Rate'].value

    @dbus_property(access=PropertyAccess.READ)
    def RssiThreshold(self) -> 'u':
        return self.props['RssiThreshold'].value

    @dbus_property(access=PropertyAccess.READ)
    def ErrorRateThreshold(self) -> 'b':
        return self.props['ErrorRateThreshold'].value

    @dbus_property(access=PropertyAccess.READ)
    def Cdma(self) -> 'a{sv}':
        return self.props['Cdma'].value

    @dbus_property(access=PropertyAccess.READ)
    def Evdo(self) -> 'a{sv}':
        return self.props['Evdo'].value

    @dbus_property(access=PropertyAccess.READ)
    def Gsm(self) -> 'a{sv}':
        return self.props['Gsm'].value

    @dbus_property(access=PropertyAccess.READ)
    def Umts(self) -> 'a{sv}':
        return self.props['Umts'].value

    @dbus_property(access=PropertyAccess.READ)
    def Lte(self) -> 'a{sv}':
        return self.props['Lte'].value

    @dbus_property(access=PropertyAccess.READ)
    def Nr5g(self) -> 'a{sv}':
        return self.props['Nr5g'].value
