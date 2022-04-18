import time
from functools import reduce

import serial
import serial.tools.list_ports


class AppToken(serial.Serial):
    ERR_NONE = '\x00'

    _INIT = '\xAA\xDD\x00'

    # Color
    _RED = '\x01'
    _GREEN = '\x02'
    _NONE = '\x00'

    # Command code
    _INFO = '\x01\x02'  # Data None
    _BEEP = '\x01\x03'  # + Data Duration (default int=0)
    _COLOR = '\x01\x04'  # + Data Color (01=red / 02=green / 00=none)
    _READ_TAG = '\x01\x0C'  # Data None
    _WRITE_TAG = '\x02\x0C'  # + Data (00=по умолчанию / 01=блокировка # (токен будет доступен только для чтения!)
    # затем (5 байт) данные карты
    _WRITE_TAG_RESERVE = '\x03\x0C'  # + Data (00=по умолчанию / 01=блокировка # (токен будет доступен только для
    # чтения!) затем (5 байт) данные карты
    _STATUS = False

    def __init__(self, uart_port, bauds=38400, debug=False):
        if uart_port.find("/") == -1:
            uart_port = "/dev/" + uart_port
        serial.Serial.__init__(self, uart_port, bauds, 8, serial.PARITY_NONE, timeout=0)
        self._debug = debug
        # self.list_port()
        if not self._STATUS:
            self.init()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, val):
        self._debug = val

    def init(self):
        if self.get_info():
            self.set_led(self._GREEN)
            self._STATUS = True

    @staticmethod
    def list_port():
        ports = [port for port in serial.tools.list_ports.comports()]
        print('=' * 28, 'Default ports', '=' * 28)
        for port in ports:
            print(f'{port}')
        print('=' * 71, '\n')

    def _execute(self, opcode, data="", check_result=None):

        assert (len(opcode) == 2 and len(data) <= 252)
        opcode_data = opcode + data
        cmd = self._INIT + chr(len(opcode_data) + 1) + opcode_data + self._checksum(opcode_data)

        if self._debug:
            print(f'>> {self._strtohex(cmd)}')

        self.write(bytearray.fromhex(self._strtohex(cmd)))
        time.sleep(0.1)

        # get result
        result = self.read()
        time.sleep(0.1)
        if result == "":
            raise IOError("operation timed out")
        result += self.read(1000)

        if self._debug:
            print(f'<< {self._tohexstring(result)}')

        if len(result) < 4 or result[3] != len(result) - 4:
            return f"answer bad length: {self._tohexstring(result)}"
        if self._tohexstring(result[:3]) != self._strtohex(self._INIT) or \
                self._tohexstring(result[4:6]) != self._strtohex(opcode):
            return f"answer bad format: {self._tohexstring(result)}"

        status = result[6]

        if check_result and status != ord(check_result):
            return f"rfid command error #{status}"

        data = result[7:-1]
        if opcode == self._READ_TAG:
            data = result[-6:-1]

        if opcode == self._INFO:
            return status, data
        return status, data.hex(' ', -1).upper()

    @staticmethod
    def _strtohex(s, sep=" "):
        return sep.join(map(lambda c: format(ord(c), '02X'), s))

    @staticmethod
    def _tohexstring(args):
        return args.hex(" ", -1).upper()

    @staticmethod
    def _tochar(args):
        out = ''
        for i in args.split():
            out += chr(int(i, 16))
        return out

    @staticmethod
    def _checksum(code):
        return chr(reduce(lambda hi, lo: hi ^ ord(lo), code, 0))

    def beep(self, duration=10):
        return self._execute(self._BEEP, chr(duration), check_result=self.ERR_NONE)[0]

    def set_led(self, code):
        return self._execute(self._COLOR, code, check_result=self.ERR_NONE)[0]

    def get_info(self):
        return self._execute(self._INFO, check_result=self.ERR_NONE)[1]

    def read_token(self):
        return self._execute(self._READ_TAG, check_result=self.ERR_NONE)[1]

    def write_token(self, data, lock=False):
        lock = "\x01" if lock else "\x00"
        tmp_token = self._tochar(data)
        return self._execute(self._WRITE_TAG_RESERVE, lock + tmp_token, check_result=self.ERR_NONE)[0]


"""
    if __name__ == "__main__":
        token = AppToken('/dev/ttyUSB0', debug=False)
    
        # Color
        _RED = '\x01'
        _GREEN = '\x02'
        _NONE = '\x00'
    
        def check(tmp):
            return {
                tmp == 0: "OK",
                tmp == 1: "Fail"
            }[True]
    
    
        print(f"Led status: {check(token.set_led(_GREEN))}")
        print(f"Beep status: {check(token.beep(5))}")
        print("INFO: " + token.get_info().decode())
        #
        user_token = token.read_token()
        print("Token: " + user_token)
        # with open('tokens.txt', 'a') as f:
        #     f.write(f'{user_token}\n')
        # print(f"Write status: {token.write_token('56 5A 9F EA C9', lock=False)}")
"""
