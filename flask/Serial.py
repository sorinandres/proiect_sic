import serial

class Serial:

    def __init__(self, port = 0, baudrate = 0):

        self.ok = True

        if port == 0 or baudrate == 0:
            self.ok = False
            return

        self.ser = serial.Serial(port, baudrate)

    def write(self, data):
        if self.ok:
            self.ser.write(data)

    def read(self):
        if self.ok:
            return self.ser.read()


    def turnHRVledOn(self):
        if self.ok:
            self.ser.write(b'1')

    def turnHRVledOff(self):
        if self.ok:
            self.ser.write(b'0')

    def turnBPMledOn(self):
        if self.ok:
            self.ser.write(b'3')

    def turnBPMledOff(self):
        if self.ok:
            self.ser.write(b'2')

    def turnRRledOn(self):
        if self.ok:
            self.ser.write(b'5')

    def turnRRledOff(self):
        if self.ok:
            self.ser.write(b'4')

    def blinkALLleds(self):
        if self.ok:
            self.ser.write(b'6')

    def turnALLledsOff(self):
        if self.ok:
            self.ser.write(b'7')

    def close(self):
        if self.ok:
            self.ser.close()
    