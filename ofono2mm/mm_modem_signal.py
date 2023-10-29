from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemSignalInterface(ServiceInterface):
    def __init__(self, modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Signal')
        self.modem = modem
        self.rate = 0
        self.rssi_threshold = 0
        self.error_rate_threshold = False
        self.set_signal_props()

    def set_signal_props(self):
        self.signal_properties = {
            'Cdma': Variant('a{sv}', {'rssi': Variant('d', -80), 'ecio': Variant('d', -10), 'error-rate': Variant('d', 0)}),
            'Evdo': Variant('a{sv}', {'rssi': Variant('d', -85), 'ecio': Variant('d', -12), 'error-rate': Variant('d', 0)}),
            'Gsm': Variant('a{sv}', {'rssi': Variant('d', -75), 'error-rate': Variant('d', 0)}),
            'Umts': Variant('a{sv}', {'rssi': Variant('d', -70), 'error-rate': Variant('d', 0)}),
            'Lte': Variant('a{sv}', {'rssi': Variant('d', -65), 'error-rate': Variant('d', 0)}),
            'Nr5g': Variant('a{sv}', {'rssi': Variant('d', -60), 'error-rate': Variant('d', 0)})
        }

    @method()
    def Setup(self, rate: 'u'):
        self.rate = rate

    @method()
    def SetupThresholds(self, settings: 'a{sv}'):
        self.rssi_threshold = settings.get('rssi-threshold', Variant('u', 0)).value
        self.error_rate_threshold = settings.get('error-rate-threshold', Variant('b', False)).value

    @dbus_property(access=PropertyAccess.READ)
    def Rate(self) -> 'u':
        return self.rate

    @dbus_property(access=PropertyAccess.READ)
    def RssiThreshold(self) -> 'u':
        return self.rssi_threshold

    @dbus_property(access=PropertyAccess.READ)
    def ErrorRateThreshold(self) -> 'b':
        return self.error_rate_threshold

    @dbus_property(access=PropertyAccess.READ)
    def Cdma(self) -> 'a{sv}':
        return self.signal_properties.get('Cdma', Variant('a{sv}', {})).value

    @dbus_property(access=PropertyAccess.READ)
    def Evdo(self) -> 'a{sv}':
        return self.signal_properties.get('Evdo', Variant('a{sv}', {})).value

    @dbus_property(access=PropertyAccess.READ)
    def Gsm(self) -> 'a{sv}':
        return self.signal_properties.get('Gsm', Variant('a{sv}', {})).value

    @dbus_property(access=PropertyAccess.READ)
    def Umts(self) -> 'a{sv}':
        return self.signal_properties.get('Umts', Variant('a{sv}', {})).value

    @dbus_property(access=PropertyAccess.READ)
    def Lte(self) -> 'a{sv}':
        return self.signal_properties.get('Lte', Variant('a{sv}', {})).value

    @dbus_property(access=PropertyAccess.READ)
    def Nr5g(self) -> 'a{sv}':
        return self.signal_properties.get('Nr5g', Variant('a{sv}', {})).value
