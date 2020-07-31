#!/usr/bin/python3

import sys
import threading
import queue
import pyaudio
import configparser
import time

class SoundCardReader(threading.Thread):
    def __init__(self, global_config, encoderQ, thread_control):
        threading.Thread.__init__(self)
        self.thread_control = thread_control
        self.encoderQ = encoderQ

        self.FORMAT = pyaudio.paInt16

        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 512
        self.DEV = 'default'
        self.TIMELIMIT = 0
        if 'input' in global_config:
            config = global_config['input']
            self.CHANNELS = config.getint('Channels', self.CHANNELS)
            self.RATE = config.getint('Rate', self.RATE)
            self.CHUNK = config.getint('ChunkSize', self.CHUNK)
            self.DEV = config.get('Device', self.DEV)
            self.TIMELIMIT = config.getint('Timelimit', self.TIMELIMIT)
        self.audio = pyaudio.PyAudio()

        self.get_device_index()
        if self.DEV_INDEX is None:
            print("initialized Reader on default device")
        else:
            print("initialized Reader on %s (%d)" % (self.DEV, self.DEV_INDEX))

    def get_device_index(self):
        cards = self.audio.get_host_api_info_by_index(0)
        dev_count = cards.get('deviceCount')
        return_val = None
        print("\nEnumerated input Cards:")
        for i in range (0, dev_count):
            candidate = self.audio.get_device_info_by_host_api_device_index(0, i).get('name')
            if self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                print("%5d %s" % (i, candidate))
                if candidate == self.DEV:
                    return_val = i
        if return_val is None:
            print("Could not find '%s' in device list index, using index of None" % self.DEV)
        self.DEV_INDEX = return_val
        return return_val
        
    def run(self):
        in_stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                   rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
                   input_device_index=self.DEV_INDEX)
        print("input device opened")
        sys.stdout.flush()
        sample_limit = 0
        sample_count = 0
        if self.TIMELIMIT:
            sample_limit = (self.RATE * self.TIMELIMIT) / self.CHUNK
        sys.stdout.flush()
        while not self.thread_control['exit_flag']:
            try: 
                in_data = in_stream.read(self.CHUNK)
                self.encoderQ.put(in_data)
                sample_count = sample_count + 1
                if sample_limit and sample_count > sample_limit:
                    self.thread_control['exit_flag'] = 1
            except:
                print("Reader Exception: ", end="")
                print(sys.exc_info()[1])
                sys.stdout.flush()
                self.thread_control['exit_flag'] = 1
        print("Reader Exiting...")
        self.thread_control['exit_flag'] = 1
        self.encoderQ.put(b'00')
        self.audio.terminate()
