from PySide2.QtWidgets import QApplication, QFrame, QWidget
from PySide2.QtCore import QTimer
from threading import Thread
from collections import deque
import numpy as np

# All credit for audio processing to https://github.com/sbarratt/spectrum-analyzer
from spectrum_analyzer import SpectrumAnalyzer

class Smoother:
    def __init__(self):
        self.values = deque(maxlen=5)
    
    def add_sample(self, sample):
        self.values.append(sample)
    
    def get_smooth_sample(self):
        sample = []
        for index in range(len(self.values[0])):
            to_be_meaned = []
            divisor = 0
            for item in list(self.values):
                #to_be_meaned.append(item[index])
                to_be_meaned.append(item[index] * 2**index+1)
                divisor += 2**index+1
            #sample.append(mean(to_be_meaned))
            sample.append(sum(to_be_meaned) / divisor)
        #return sample
        return self.smoothListGaussian(sample)

    def smoothListGaussian(self, sample, degree=3):
        # There are probably better smoothing algorithms for this.
        # https://swharden.com/wp/2008-11-17-linear-data-smoothing-in-python/
        window = degree*2-1
        weight = np.array([1.0]*window)
        weightGauss = []
        for i in range(window):
            i = i-degree+1
            frac = i/float(window)
            gauss = 1/(np.exp((4*(frac))**2))
            weightGauss.append(gauss)
        weight = np.array(weightGauss)*weight
        smoothed = [0.0]*(len(sample)-window)
        for i in range(len(smoothed)):
            smoothed[i] = sum(np.array(sample[i:i+window])*weight)/sum(weight)
        return smoothed

class Visualizer(QFrame):
    def __init__(self, parent, bars=25, color="white"):
        super().__init__(parent)

        self.frames = []
        self.bars_count = bars

        for _ in range(bars):
            x = QFrame(self)
            x.setStyleSheet(f"background-color: {color};")
            self.frames.append(x)
        
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(16)
        self.update_timer.timeout.connect(self.update_graph)
        self.update_timer.start()

        self.audio_getter = SpectrumAnalyzer()
        self.smoother = Smoother()

        self.groups = self._get_audio_groups(bars + 5)

        self.current_sample = [0] * (bars + 5)

        self.audio_update_thread = Thread(target = self.update_audio_data)
        self.audio_update_thread.start()

    def resizeEvent(self, event):
            x = 0
            for item in self.frames:
                item.resize((self.width() - (3 * self.bars_count)) / self.bars_count, 2)
                item.move(((self.width() - (3 * self.bars_count)) / self.bars_count) * x + 3 * x, 0)
                x += 1

    def _get_audio_groups(self, count):
        # frequency range of audio data
        audio_range = list(range(0, 24000, 20))
        # Base of exponential scale
        base = 11
        # Step of exponent in each group
        step = (4 - 1) / count

        # List of exponent powers of 11
        powers = [1+step]
        for _ in range(count):
            powers.append(powers[-1]+step)

        # List of tuple pairs of ranges per bar
        frequency_ranges = []
        for item in powers[:-1]:
            frequency_ranges.append((11**item, 11**powers[powers.index(item) + 1]))

        # Create groups of what indexes to slice audio data at.
        groups = []
        for pair_1, pair_2 in frequency_ranges:
            start = None
            end = None
            for item in audio_range:
                if not start and item > pair_1:
                    start = audio_range.index(item)
                if not end and item > pair_2:
                    end = audio_range.index(item) - 1
            '''if len(groups) > 3:
                if groups[-1][0] >= start and groups[-1][1] >= end + 1:
                    start = groups[-1][1]
                    end = start + 1'''
            groups.append((start, end + 1))

        return groups

    def update_audio_data(self):
        while True:
            try:
                data = self.audio_getter.readData()
            except:
                continue
            
            #print(f"Audio Data took {time.perf_counter() - t1:.4f} seconds")
            f, Pxx = self.audio_getter.get_spectrum(data)
            Pxx = Pxx[1200:]

            self.current_sample = []
            for start, end in self.groups:
                if start <= end:
                    end = start + 1
                self.current_sample.append(max(Pxx[start:end]))

    def update_graph(self):
        self.smoother.add_sample(self.current_sample)
        smooth_values = self.smoother.get_smooth_sample()
        for index in range(len(self.current_sample)):
            try:
                self.frames[index].resize((self.width() - (3 * self.bars_count)) / self.bars_count, smooth_values[index])
            except:
                pass

if __name__ == "__main__":
    app = QApplication()
    window = QWidget()
    vis = Visualizer(window, 25, "black") # Color can be hex as well, like #FF0000
    window.resize(400,300)
    vis.resize(400, 300)
    window.show()
    app.exec_()