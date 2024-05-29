class Packet:
    def __init__(self, ts, data):
        self.ts = ts
        self.data = data

    def get_ts(self):
        return self.ts
    
    def get_data_string(self):
        return self.data.hex()

class EcgPacket(Packet):
    def __init__(self, ts, data):
        super().__init__(ts, data)
    

    def get_samples(self):
        ecg_samples = []
        for i in range(0, len(self.data), 3):
            ecg_samples.append(int.from_bytes(self.data[i:i+3], byteorder='little', signed=True))
        return ecg_samples

    def get_data(self):
        return self.data

    PacketSampleCount = 73
    SamplingRate = 130


class AccPacket(Packet):
    def __init__(self, ts, data):
        super().__init__(ts, data)

    def get_samples(self):
        x_samples = []
        y_samples = []
        z_samples = []

        for i in range(0, len(self.data), 6):
            x_samples.append(int.from_bytes(self.data[i:i+2], byteorder='little', signed=True))
            y_samples.append(int.from_bytes(self.data[i+2:i+4], byteorder='little', signed=True))
            z_samples.append(int.from_bytes(self.data[i+4:i+6], byteorder='little', signed=True))
        
        return x_samples, y_samples, z_samples

    PacketSampleCount = 36
    SamplingRate = 25