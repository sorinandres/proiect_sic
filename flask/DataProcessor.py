import neurokit2 as nk
import numpy as np
import scipy.signal as signal



class DataProcessor:

    def __init__(self) -> None:
        self._ecg_buffer = []
        self._acc_buffer = []

        # create a butterworth filter lowpass
        self._lowcut = 0.175
        self._highcut = 0.45
        self._fs = 100

        self._b_lowpass, self._a_lowpass = signal.cheby1(7, 0.5, self._lowcut, btype='high', analog=False, output='ba', fs=self._fs)
        self._b_highpass, self._a_highpass = signal.cheby2(7, 15, self._highcut, btype='low', analog=False, output='ba', fs=self._fs)

    def process_ecg(self, ecg_packets):
        for packet in ecg_packets:
            self._ecg_buffer += packet.get_samples()

        ecg = nk.ecg_process(self._ecg_buffer, sampling_rate=130)
        self._ecg_buffer = []

        return ecg
    
    def lowpass_filter(self, x, y, z):
        x_filt = signal.filtfilt(self._b_lowpass, self._a_lowpass, x)
        y_filt = signal.filtfilt(self._b_lowpass, self._a_lowpass, y)
        z_filt = signal.filtfilt(self._b_lowpass, self._a_lowpass, z)

        return x_filt, y_filt, z_filt
    
    def highpass_filter(self, x, y, z):
        x_filt = signal.filtfilt(self._b_highpass, self._a_highpass, x)
        y_filt = signal.filtfilt(self._b_highpass, self._a_highpass, y)
        z_filt = signal.filtfilt(self._b_highpass, self._a_highpass, z)

        return x_filt, y_filt, z_filt
    
    def get_bpm_hrv(self, ecg_signal):

        ecg_signal, info = nk.ecg_process(ecg_signal, sampling_rate=130)
        mean_ecg_rate = int(ecg_signal["ECG_Rate"].mean())
        hrv = nk.hrv_time(ecg_signal, sampling_rate=130, show=False)
        sdnn = int(hrv["HRV_SDNN"].values[0])

        return mean_ecg_rate, sdnn

    def process_acc(self, x, y, z):
        
        x, y, z = self.lowpass_filter(x, y, z)
        x_filt, y_filt, z_filt = self.highpass_filter(x, y, z)

        cov_matrix = np.cov([x_filt, y_filt, z_filt])
        eig_values, eig_vectors = np.linalg.eig(cov_matrix)

        w1 = eig_values[0] / np.sum(eig_values)
        w2 = eig_values[1] / np.sum(eig_values)
        w3 = eig_values[2] / np.sum(eig_values)

        combined_signal = w1 * x_filt + w2 * y_filt + w3 * z_filt

        frequencies, power_spectrum = signal.periodogram(combined_signal, self._fs)
    
        # get the frequency in the range 0.2 - 0.7 Hz
        mask = (frequencies >= self._lowcut) & (frequencies <= self._highcut)
        frequencies = frequencies[mask]
        power_spectrum = power_spectrum[mask]

        # find the frequency with the maximum power
        max_power_index = np.argmax(power_spectrum)
        max_power_frequency = frequencies[max_power_index]

        # find the weighted mean frequency with frequencies with power greater than 1/2 of the dominant frequency
        mask = power_spectrum > power_spectrum[max_power_index] / 2
        masked_freq = frequencies[mask]
        weighted_mean_frequency = np.average(masked_freq, weights=power_spectrum[mask])

        # # get max power frequency
        # max_power_frequency = frequencies[np.argmax(power_spectrum)]

        # weighted_mean_frequency = max_power_frequency

        return weighted_mean_frequency * 60