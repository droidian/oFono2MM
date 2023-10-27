from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess

class MMModemOmaInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Oma')
        self._features = 0
        self._pending_network_initiated_sessions = []
        self._session_type = 0
        self._session_state = 0

    @method()
    def Setup(self, features: 'u'):
        self._features = features
        pass

    @method()
    def StartClientInitiatedSession(self, session_type: 'u'):
        self._session_type = session_type
        pass

    @method()
    def AcceptNetworkInitiatedSession(self, session_id: 'u', accept: 'b'):
        if accept:
            self._pending_network_initiated_sessions = [
                s for s in self._pending_network_initiated_sessions if s[1] != session_id
            ]
        pass

    @method()
    def CancelSession(self):
        pass

    @signal()
    def SessionStateChanged(self, old_session_state: 'i', new_session_state: 'i', session_state_failed_reason: 'u'):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def Features(self) -> 'u':
        return self._features

    @dbus_property(access=PropertyAccess.READ)
    def PendingNetworkInitiatedSessions(self) -> 'a(uu)':
        return self._pending_network_initiated_sessions

    @dbus_property(access=PropertyAccess.READ)
    def SessionType(self) -> 'u':
        return self._session_type

    @dbus_property(access=PropertyAccess.READ)
    def SessionState(self) -> 'i':
        return self._session_state
