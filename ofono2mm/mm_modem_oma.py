from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMModemOmaInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Oma')
        self.mm_modem = mm_modem
        self.props = {
            'Features': Variant('u', 0),
            'PendingNetworkInitiatedSessions': Variant('a(uu)', []),
            'SessionType': Variant('u', 0), # on runtime unknown MM_OMA_SESSION_TYPE_UNKNOWN
            'SessionState': Variant('i', 0) # hardcoded value unknown MM_OMA_SESSION_STATE_UNKNOWN
        }

    @method()
    def Setup(self, features: 'u'):
        self.props['Features'] = Variant('u', features)

    @method()
    def StartClientInitiatedSession(self, session_type: 'u'):
        self.props['SessionType'] = Variant('u', session_type)

    @method()
    def AcceptNetworkInitiatedSession(self, session_id: 'u', accept: 'b'):
        pass

    @method()
    def CancelSession(self):
        pass

    @signal()
    def SessionStateChanged(self, old_session_state: 'i', new_session_state: 'i', session_state_failed_reason: 'u'):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def Features(self) -> 'u':
        return self.props['Features'].value

    @dbus_property(access=PropertyAccess.READ)
    def PendingNetworkInitiatedSessions(self) -> 'a(uu)':
        return self.props['PendingNetworkInitiatedSessions'].value

    @dbus_property(access=PropertyAccess.READ)
    def SessionType(self) -> 'u':
        return self.props['SessionType'].value

    @dbus_property(access=PropertyAccess.READ)
    def SessionState(self) -> 'i':
        return self.props['SessionState'].value
