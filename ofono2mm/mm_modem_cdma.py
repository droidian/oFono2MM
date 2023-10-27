from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)

class MMModemCDMAInterface(ServiceInterface):

    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.ModemCdma')
        self.mm_modem = mm_modem

    @method()
    def Activate(self, carrier_code: 's'):
        pass

    @method()
    def ActivateManuel(self, properties: 'a{sv}') -> 'o':
        pass
