from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant
from datetime import datetime
import gi
gi.require_version('Geoclue', '2.0')
from gi.repository import Geoclue

class MMModemLocationInterface(ServiceInterface):
    def __init__(self, modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Location')
        self.modem = modem

        self.capabilities = 0
        self.supported_assistance_data = 0
        self.enabled = 0
        self.signals_location = False
        self.location = {}
        self.supl_server = ""
        self.assistance_data_servers = []
        self.gps_refresh_rate = 30

        self.geoclue = Geoclue.Simple.new_sync('ModemManager', Geoclue.AccuracyLevel.NEIGHBORHOOD, None)

    @method()
    def Setup(self, sources: 'u', signal_location: 'b') -> None:
        if sources == 1:
            self.enabled = 1
        else:
            self.enabled = 0

        if signal_location is True:
            self.signals_location = True
        else:
            self.signals_location = False

    @method()
    def GetLocation(self) -> 'a{uv}':
        location = self.geoclue.get_location()
        latitude = location.get_property('latitude')
        longitude = location.get_property('longitude')
        utc_time = datetime.utcnow().isoformat()

        self.location = {
            'utc-time': Variant('s', utc_time),
            'latitude': Variant('d', latitude),
            'longitude': Variant('d', longitude)
        }

        # has to be tested more, it gathers correctly tho
        # return self.location
        return {}

    @method()
    def SetSuplServer(self, supl: 's') -> None:
        self.supl_server = supl

    @method()
    def InjectAssistanceData(self, data: 'ay') -> None:
        pass

    @method()
    def SetGpsRefreshRate(self, rate: 'u') -> None:
        self.gps_refresh_rate = rate

    @dbus_property(access=PropertyAccess.READ)
    def Capabilities(self) -> 'u':
        return self.capabilities

    @dbus_property(access=PropertyAccess.READ)
    def SupportedAssistanceData(self) -> 'u':
        return self.supported_assistance_data

    @dbus_property(access=PropertyAccess.READ)
    def Enabled(self) -> 'u':
        return self.enabled

    @dbus_property(access=PropertyAccess.READ)
    def SignalsLocation(self) -> 'b':
        return self.signals_location

    @dbus_property(access=PropertyAccess.READ)
    def Location(self) -> 'a{uv}':
        return self.location

    @dbus_property(access=PropertyAccess.READ)
    def SuplServer(self) -> 's':
        return self.supl_server

    @dbus_property(access=PropertyAccess.READ)
    def AssistanceDataServers(self) -> 'as':
        return self.assistance_data_servers

    @dbus_property(access=PropertyAccess.READ)
    def GpsRefreshRate(self) -> 'u':
        return self.gps_refresh_rate
