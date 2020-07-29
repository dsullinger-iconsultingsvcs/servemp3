#!/usr/bin/python3

import threading
import queue
import lameenc
import configparser

class PassthruEncoder(threading.Thread):
    def __init__(self, global_config, encoderQ, writerQ, thread_control):
        threading.Thread.__init__(self)
        self.thread_control = thread_control
        self.encoderQ = encoderQ
        self.writerQ = writerQ
        print("initialized Passthrough Encoder")
    def run(self):
        while not self.thread_control['exit_flag']:
            itm = self.encoderQ.get()
            if itm != b'00':
                self.writerQ.put(itm)
        print("Passthrough Encoder exiting...")
        self.thread_control['exit_flag'] = 1
        self.writerQ.put(b'00')


class MP3Encoder(threading.Thread):
    def __init__(self, global_config, encoderQ, writerQ, thread_control):
        threading.Thread.__init__(self)
        self.thread_control = thread_control
        self.encoderQ = encoderQ
        self.writerQ = writerQ

        self.BITRATE = 192
        self.SAMPLERATE = int(global_config.get('input','Rate',fallback='44100'))
        self.CHANNELS = int(global_config.get('input','Channels',fallback='1'))
        self.QUALITY = 2
        if 'encoding' in global_config:
            config = global_config['encoding']
            self.BITRATE = config.getint('BitRate', self.BITRATE)
            self.SAMPLERATE = config.getint('SampleRate', self.SAMPLERATE)
            self.CHANNELS = config.getint('Channels', self.CHANNELS)
            self.QUALITY = config.getint('Quality', self.QUALITY)

        self.encoder = lameenc.Encoder()
        self.encoder.set_bit_rate(self.BITRATE)
        self.encoder.set_in_sample_rate(self.SAMPLERATE)
        self.encoder.set_channels(self.CHANNELS)
        self.encoder.set_quality(self.QUALITY)
        print("initialized MP3 Encoder %dkbps,%dkHz,%d channels,%d quality" % (self.BITRATE, self.SAMPLERATE, self.CHANNELS, self.QUALITY))
    def run(self):
        while not self.thread_control['exit_flag']:
            itm = self.encoderQ.get()
            if itm != b'00':
                mp3_data = self.encoder.encode(itm)
                itm = mp3_data
                self.writerQ.put(mp3_data)
        print("MP3 Encoder exiting...")
        self.thread_control['exit_flag'] = 1
        self.writerQ.put(b'00')
