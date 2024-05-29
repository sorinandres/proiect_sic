from typing import List
from Device import Device
from Adapter import Adapter
from DataProcessor import DataProcessor
import websocket_server
import time
import neurokit2 as nk
from Packet import EcgPacket, AccPacket
from Serial import Serial
import subprocess

MESSAGE_ECG_SAMPLES     = "1000 "
MESSAGE_ECG_BPM_10S     = "1001 "
MESSAGE_ECG_HRV_10S     = "1002 "
MESSAGE_ACC_SAMPLES_X   = "1003 "
MESSAGE_ACC_SAMPLES_Y   = "1004 "
MESSAGE_ACC_SAMPLES_Z   = "1005 "
MESSAGE_RESPIRATION     = "1006 "
MESSAGE_ECG_BPM_60S     = "1007 "
MESSAGE_ECG_HRV_60S     = "1008 "


class PolarApp:

    def __init__(self):

        self._serial = Serial()

        try:
            self._serial : Serial = Serial(port="/dev/ttyUSB0", baudrate=9600)
            self._serial.blinkALLleds()
        except:
            print("Could not connect to the _serial port")
        
        self._serial.blinkALLleds()

        time.sleep(0.2)

        self.adapter = Adapter()
        self.adapter.set_callback_on_scan_start()
        self.adapter.set_callback_on_scan_stop()
        self.adapter.set_callback_on_scan_found()

        self.ws = websocket_server.WebsocketServer("0.0.0.0", 5001)
        self.ws.run_forever(threaded=True)

        self.dp = DataProcessor()

        self.signal_stop = False

        self.running = False

    def scan(self, device_name : str = "Polar H10 88D41D21") -> str:
        try:
            peripherals = self.adapter.scan(5000)
        except:
            return "Could not scan for devices"
        
        self.peripheral = self.adapter.get_peripheral(device_name)

        if self.peripheral is None:
            return "Could not find device"
        
    def connect(self) -> bool:
        try:
            self.device = Device(self.peripheral)
            self.device.connect()
        except:
            return False
        
        return True
    
    def reset(self):
        subprocess.run(["sudo", "hciconfig", "hci0", "reset"])

    def disconnect(self):
        self.device.disconnect()

    def is_connected(self):
        return self.peripheral.is_connected()

    def start_ecg_stream(self):
        self.device.start_ecg_stream()

    def start_acc_stream(self):
        self.device.start_acc_stream()

    def stop_ecg_stream(self):
        self.device.stop_ecg_stream()

    def stop_acc_stream(self):
        self.device.stop_acc_stream()

    def send_samples(self, message_header : str, samples : list):
        message = message_header
        for sample in samples:
            message += str(sample) + " "

        self.ws.send_message_to_all(message)

    def run(self):

        while not self.is_connected():
            time.sleep(0.2)            

        self.start_ecg_stream()
        self.start_acc_stream()

        self.ecgDataFile = open("ecgData.txt", "w")
        self.accDataFile = open("accData.txt", "w")

        ecg_packets_buffer : List[EcgPacket] = []
        acc_packets_buffer : List[AccPacket] = []

        ecg_packets_to_process : List[EcgPacket] = []
        acc_packets_to_process : List[AccPacket] = []

        ecg_packets_to_process_60 : List[EcgPacket] = []

        acc_packets_to_send : List[EcgPacket] = []
        ecg_packets_to_send : List[AccPacket] = []

        T_ecg = 1/130
        T_acc = 1/100

        ECG_SAMPLES_PER_PACKET = 73
        ACC_SAMPLES_PER_PACKET = 36

        def one_minute_of_data(T, samples_per_packet):
            return int(60 / (T * samples_per_packet))

        self.running = True

        try:
            self._serial.turnALLledsOff()
        except:
            pass

        bpm10s = 0
        hrv10s = 0

        bpm60s = 0
        hrv60s = 0

        while True:

            if self.signal_stop:
                self.running = False
                self.signal_stop = False
                self.accDataFile.close()
                self.ecgDataFile.close()
                try:
                    self._serial.blinkALLleds()
                except:
                    pass
                break

            ecg_packets_buffer += self.device.get_ecg_packets()
            acc_packets_buffer += self.device.get_acc_packets()

            ecg_packets_to_process += ecg_packets_buffer
            acc_packets_to_process += acc_packets_buffer

            ecg_packets_to_process_60 += ecg_packets_buffer

            ecg_packets_to_send += ecg_packets_buffer
            acc_packets_to_send += acc_packets_buffer

            for packet in ecg_packets_buffer:
                for sample in packet.get_samples():
                    self.ecgDataFile.write(str(sample) + "\n")

            for packet in acc_packets_buffer:
                x, y, z = packet.get_samples()
                for i in range(len(x)):
                    self.accDataFile.write(str(x[i]) + " " + str(y[i]) + " " + str(z[i]) + "\n")

            ecg_packets_buffer = [] 
            acc_packets_buffer = []

            ecg_signal = []
            for ecg_packet in ecg_packets_to_send:
                ecg_signal += ecg_packet.get_samples()

            if ecg_signal == []:
                time.sleep(0.2)
                continue

            self.send_samples(MESSAGE_ECG_SAMPLES, ecg_signal)
            ecg_packets_to_send = []

            

            if len(ecg_packets_to_process) > one_minute_of_data(T_ecg, ECG_SAMPLES_PER_PACKET)//6:
                # print("Processing ECG data 10 seconds")

                ecg_signal = []
                for ecg_packet in ecg_packets_to_process:
                    ecg_signal += ecg_packet.get_samples()

                bpm, hrv = self.dp.get_bpm_hrv(ecg_signal)

                bpm10s = bpm
                hrv10s = hrv

                self.ws.send_message_to_all(MESSAGE_ECG_BPM_10S + str(bpm))
                self.ws.send_message_to_all(MESSAGE_ECG_HRV_10S + str(hrv))

                ecg_packets_to_process = []

            if len(ecg_packets_to_process_60) > one_minute_of_data(T_ecg, ECG_SAMPLES_PER_PACKET):
                # print("Processing ECG data 60 seconds")

                ecg_signal = []
                for ecg_packet in ecg_packets_to_process_60:
                    ecg_signal += ecg_packet.get_samples()

                bpm, hrv = self.dp.get_bpm_hrv(ecg_signal)

                self.ws.send_message_to_all(MESSAGE_ECG_BPM_60S + str(bpm))
                self.ws.send_message_to_all(MESSAGE_ECG_HRV_60S + str(hrv))

                bpm60s = bpm
                hrv60s = hrv

                ecg_packets_to_process_60 = []

            try:
                if (bpm10s < 60 and bpm10s > 0) or (bpm10s > 100) or (bpm60s < 60 and bpm60s > 0) or (bpm60s > 100):
                    self._serial.turnBPMledOn()

                else:
                    self._serial.turnBPMledOff()

                if (hrv10s <= 20 and hrv10s > 0) or (hrv60s <= 20 and hrv60s > 0):
                    self._serial.turnHRVledOn()
                else:
                    self._serial.turnHRVledOff()
            except:
                pass

            if len(acc_packets_to_send) > one_minute_of_data(T_acc, ACC_SAMPLES_PER_PACKET)//6:

                x_acc_samples = []
                y_acc_samples = []
                z_acc_samples = []

                for acc_packet in acc_packets_to_send:
                    x_acc_samples_buffer, y_acc_samples_buffer, z_acc_samples_buffer = acc_packet.get_samples()
                    x_acc_samples += x_acc_samples_buffer
                    y_acc_samples += y_acc_samples_buffer
                    z_acc_samples += z_acc_samples_buffer

                x_acc_samples, y_acc_samples, z_acc_samples = self.dp.lowpass_filter(x_acc_samples, y_acc_samples, z_acc_samples)
                x_acc_samples, y_acc_samples, z_acc_samples = self.dp.highpass_filter(x_acc_samples, y_acc_samples, z_acc_samples)

                # round the values
                x_acc_samples = [round(sample, 2) for sample in x_acc_samples]
                y_acc_samples = [round(sample, 2) for sample in y_acc_samples]
                z_acc_samples = [round(sample, 2) for sample in z_acc_samples]


                self.send_samples(MESSAGE_ACC_SAMPLES_X, x_acc_samples)
                self.send_samples(MESSAGE_ACC_SAMPLES_Y, y_acc_samples)
                self.send_samples(MESSAGE_ACC_SAMPLES_Z, z_acc_samples)

                acc_packets_to_send = []

            if len(acc_packets_to_process) > one_minute_of_data(T_acc, ACC_SAMPLES_PER_PACKET)//6:

                x_acc_samples = []
                y_acc_samples = []
                z_acc_samples = []

                for acc_packet in acc_packets_to_process:
                    x_acc_samples_buffer, y_acc_samples_buffer, z_acc_samples_buffer = acc_packet.get_samples()
                    x_acc_samples += x_acc_samples_buffer
                    y_acc_samples += y_acc_samples_buffer
                    z_acc_samples += z_acc_samples_buffer

                acc_packets_to_process = []

                rr = self.dp.process_acc(x_acc_samples, y_acc_samples, z_acc_samples)
                rr = int(rr)

                try:
                    if rr >= 20:
                        self._serial.turnRRledOn()
                    else:
                        self._serial.turnRRledOff()
                except:
                    pass

                self.ws.send_message_to_all(MESSAGE_RESPIRATION + str(rr))

