#!/usr/bin/python

# https://github.com/sbarratt/spectrum-analyzer
# This is a stripped down version with UI removed.

"""
PyAudio + PyQtGraph Spectrum Analyzer
Author:@sbarratt
Date Created: August 8, 2015
"""

import pyaudio
import struct
import math
import sys
import numpy as np

# Audio Format (check Audio MIDI Setup if on Mac)
FORMAT = pyaudio.paInt16
RATE = 48000
CHANNELS = 1

# Set Plot Range [-RANGE,RANGE], default is nyquist/2
RANGE = 20000
if not RANGE:
    RANGE = RATE/2

# Set these parameters (How much data to plot per FFT)
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)

# Which Channel? (L or R)
LR = "l"

class SpectrumAnalyzer():
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.initMicrophone()
    def find_input_device(self):
        device_index = None            
        for i in range(self.pa.get_device_count()):     
            devinfo = self.pa.get_device_info_by_index(i)   
            if devinfo["name"].lower() in ["mic","input"]:
                device_index = i

        return device_index

    def initMicrophone(self):
        device_index = self.find_input_device()

        self.stream = self.pa.open( format = FORMAT,
                                    channels = CHANNELS,
                                    rate = RATE,
                                    input = True,
                                    input_device_index = device_index,
                                    frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

    def readData(self):
        block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        if CHANNELS == 1:
            return np.array(shorts)
        else:
            l = shorts[::2]
            r = shorts[1::2]
            if LR == 'l':
                return np.array(l)
            else:
                return np.array(r)

    def close(self):
        sys.exit()
        self.stream.close()
        sys.exit()

    def get_spectrum(self, data):
        T = 1.0/RATE
        N = data.shape[0]
        Pxx = (1./N)*np.fft.fft(data)
        f = np.fft.fftfreq(N,T)
        Pxx = np.fft.fftshift(Pxx)
        f = np.fft.fftshift(f)

        return f.tolist(), (np.absolute(Pxx)).tolist()
