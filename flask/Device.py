import simplepyble
import time
from threading import Lock
from Packet import EcgPacket, AccPacket

class SERVICE_UUID:
    PMD = "fb005c80-02e7-f387-1cad-8acd2d8df0c8"

class CHARACTERISTIC_UUID:
    PMD_CONTROL = "fb005c81-02e7-f387-1cad-8acd2d8df0c8"
    PMD_DATA = "fb005c82-02e7-f387-1cad-8acd2d8df0c8"

class OPCODE:
    ECG_START_STREAM = b'\x02\x00\x00\x01\x82\x00\x01\x01\x0E\x00'
    ECG_STOP_STREAM = b'\x03\x00'

    ACC_START_STREAM = b'\x02\x02\x02\x01\x08\x00\x00\x01\x64\x00\x01\x01\x10\x00'
    ACC_STOP_STREAM = b'\x03\x02'



class Device:

    def __init__(self, peripheral : simplepyble.Peripheral):
        self.peripheral = peripheral
        self.ecg_packets = []
        self.acc_packets = []

        self._acc_cf = 0
        self._ecg_cf = 0

        self.ecg_lock = Lock()
        self.acc_lock = Lock()

    def connect(self):
        self.peripheral.connect()
        self.peripheral.notify(SERVICE_UUID.PMD, CHARACTERISTIC_UUID.PMD_DATA, self.__notify_callback)

    def start_ecg_stream(self):
        self.peripheral.write_request(SERVICE_UUID.PMD, CHARACTERISTIC_UUID.PMD_CONTROL, OPCODE.ECG_START_STREAM)

    def stop_ecg_stream(self):
        self.peripheral.write_request(SERVICE_UUID.PMD, CHARACTERISTIC_UUID.PMD_CONTROL, OPCODE.ECG_STOP_STREAM)
        self._first_ecg = False

    def start_acc_stream(self):
        self.peripheral.write_request(SERVICE_UUID.PMD, CHARACTERISTIC_UUID.PMD_CONTROL, OPCODE.ACC_START_STREAM)

    def stop_acc_stream(self):
        self.peripheral.write_request(SERVICE_UUID.PMD, CHARACTERISTIC_UUID.PMD_CONTROL, OPCODE.ACC_STOP_STREAM)
        self._first_acc = False

    def __notify_callback(self, data):
        timestamp = int.from_bytes(data[1:9], byteorder='little', signed=False)
        if data[0] == 0x02:

            if self._acc_cf > 0:
                timestamp = timestamp + self._acc_cf
            else:
                self._acc_cf = time.time_ns() - timestamp
                timestamp = timestamp + self._ecg_cf

            self.acc_lock.acquire()
            self.acc_packets.append(AccPacket(timestamp, data[10:]))
            self.acc_lock.release()

        if data[0] == 0x00:
            
            if self._ecg_cf > 0:
                timestamp = timestamp + self._ecg_cf
            else:
                self._ecg_cf = time.time_ns() - timestamp
                timestamp = timestamp + self._ecg_cf

            self.ecg_lock.acquire()
            self.ecg_packets.append(EcgPacket(timestamp, data[10:]))
            self.ecg_lock.release()

    def disconnect(self):
        self.peripheral.disconnect()

    def get_ecg_packets(self):
        self.ecg_lock.acquire()
        packets = self.ecg_packets.copy()
        self.ecg_packets.clear()
        self.ecg_lock.release()
        return packets
    
    def get_acc_packets(self):
        self.acc_lock.acquire()
        packets = self.acc_packets.copy()
        self.acc_packets.clear()
        self.acc_lock.release()
        return packets
    
    def get_ecg_packet_count(self):
        return len(self.ecg_packets)
    
    def get_acc_packet_count(self):
        return len(self.acc_packets)