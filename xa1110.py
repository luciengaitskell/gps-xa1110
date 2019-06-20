from machine import I2C, Pin

LEN = 225


class XA1110:
    def __init__(self, addr=0x10, i2c=None, verif=True):
        self._addr = addr
        if i2c is None:
            self._i2c = I2C(scl=Pin(22), sda=Pin(23), freq=100000)
        else:
            self._i2c = i2c

        if verif:
            self.verif()

    def verif(self):
        self._i2c.write(bytearray([self._addr]))

    def _read_chunk(self) -> bytes:
        return self._i2c.readfrom(self._addr, LEN)

    def read_all_data(self):
        data = []
        append_next = False

        while True:
            raw = self._read_chunk()
            strings = raw.split(b'\r')  # raw data strings, split over separate lines

            # Check if no new data:
            if len(strings) == 1 and len(strings[0].strip(b'\n')) == 0:
                # Only one string, and that string is empty (without newline chars)
                break

            for s_i, s in enumerate(strings):  # iterate through raw, potentially impartial data lines
                s = s.strip(b'\n')  # Remove all extra newline characters

                if append_next:  # append to last entry if intended
                    data[-1] += s
                elif not len(s) == 0:  # only add data if not empty
                    data.append(s)

                append_next = (s_i == len(strings) - 1 and len(s) > 0)
                # Enable append, if is last string in the set, and is not empty

        return data

    @staticmethod
    def _checksum(cstring, hex_str=True):
        """
        Generate checksum for command string.

        :param cstring: str
            Input command string
        :param hex_str: str (default=True)
            Enable return as byte string of checksum in hexadecimal, without the leading '0x'
        """
        t = 0

        for i in range(0, len(cstring)):
            t = t ^ cstring[i]

        if hex_str:
            return hex(t).strip('0x').upper().encode('ascii')

        return t

    @classmethod
    def _format_string(cls, cmd: bytes) -> bytes:
        """
        Format full command string from id and arg string.

        :param cmd: bytes
            Command string to format
        :return: bytes
        """
        cmd = b"PMTK" + cmd
        csum = cls._checksum(cmd)
        return b"$" + cmd + b"*" + csum + b"\r\n"

    def write(self, cmd: bytes):
        """ Write command to the device. """
        cmd = self._format_string(cmd)
        self._i2c.writeto(self._addr, cmd)
        return cmd
