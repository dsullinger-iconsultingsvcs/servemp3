#!/usr/bin/python3

import sys
import os.path
import threading
import queue
import pyaudio
import lameenc
import configparser
import http.server

global_config = configparser.ConfigParser()
default_config = '/etc/servemp3.config'
try:
    if os.path.exists(sys.argv[1]):
        global_config.read(sys.argv[1])
        print("user configuration used from %s" % sys.argv[1])
    else:
        global_config.read(default_config)
        print("system configuration used from %s (%s not found)" % (default_config, sys.argv[1]))
except:
    global_config.read(default_config)
    print("system configuration used from %s" % default_config)


class Reader(threading.Thread):
    def __init__(self, encoderQ, thread_control):
        threading.Thread.__init__(self)
        self.thread_control = thread_control
        self.encoderQ = encoderQ

        self.FORMAT = pyaudio.paInt16

        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 512
        if 'input' in global_config:
            config = global_config['input']
            self.CHANNELS = config.getint('Channels', self.CHANNELS)
            self.RATE = config.getint('Rate', self.RATE)
            self.CHUNK = config.getint('ChunkSize', self.CHUNK)
        self.audio = pyaudio.PyAudio()
        
        print("initialized Reader")
    def run(self):
        inStream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                   rate=self.RATE, input=True, frames_per_buffer=self.CHUNK)
        
        while not self.thread_control['exit_flag']:
            #inData = inStream.read(self.CHUNK, False)
            inData = inStream.read(self.CHUNK)
            self.encoderQ.put(inData)
        print("Reader Exiting...")
        self.thread_control['exit_flag'] = 1
        self.audio.terminate()

class Encoder(threading.Thread):
    def __init__(self, encoderQ, writerQ, thread_control):
        threading.Thread.__init__(self)
        self.thread_control = thread_control
        self.encoderQ = encoderQ
        self.writerQ = writerQ

        self.BITRATE = 192
        self.SAMPLERATE = 44100
        self.CHANNELS = 1
        self.QUALITY = 2
        if 'mp3encoding' in global_config:
            config = global_config['mp3encoding']
            self.BITRATE = config.getint('BitRate', self.BITRATE)
            self.SAMPLERATE = config.getint('SampleRate', self.SAMPLERATE)
            self.CHANNELS = config.getint('Channels', self.CHANNELS)
            self.QUALITY = config.getint('Quality', self.QUALITY)

        self.encoder = lameenc.Encoder()
        self.encoder.set_bit_rate(self.BITRATE)
        self.encoder.set_in_sample_rate(self.SAMPLERATE)
        self.encoder.set_channels(self.CHANNELS)
        self.encoder.set_quality(self.QUALITY)
        print("initialized Encoder")
    def run(self):
        while not self.thread_control['exit_flag']:
            itm = self.encoderQ.get()
            
            mp3_data = self.encoder.encode(itm)
            itm = mp3_data
            self.writerQ.put(mp3_data)
        print("Encoder exiting...")
        self.thread_control['exit_flag'] = 1

class Writer(threading.Thread):
    def __init__(self, writerQ, sock, thread_control):
        threading.Thread.__init__(self)
        self.writerQ = writerQ
        self.thread_control = thread_control
        self.sock = sock

        print("initialized Writer")
    def run(self):
        while not self.thread_control['exit_flag']:
            itm = self.writerQ.get()
            try:
                self.sock.send(itm)
            except:
                print(sys.exc_info()[1])
                self.thread_control['exit_flag'] = 1
        print("Writer exiting...")

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(s):

        ##global_config = configparser.ConfigParser()
        ##global_config.read('/etc/servemp3.config')

        encoderQueue = queue.Queue()
        writerQueue = queue.Queue()
        thread_control = {'exit_flag': 0}

        s.send_response(200)
        s.send_header("Content-type", "audio/mpeg")
        s.end_headers()

        readerThread = Reader(encoderQueue, thread_control)
        encoderThread = Encoder(encoderQueue, writerQueue, thread_control)
        writerThread = Writer(writerQueue, s.request, thread_control)

        readerThread.start()
        encoderThread.start()
        writerThread.start()
        sys.stdout.flush()

        writerThread.join()
        encoderThread.join()
        readerThread.join()

        print("All threads closed")
        sys.stdout.flush()

if __name__ == '__main__':

    port = 8080
    if 'server' in global_config:
        config = global_config['server']
        port = config.getint('port', port)
        
    with http.server.HTTPServer(("", port), RequestHandler) as httpd:
        try:
            print("Listening on port %d" % port)
            sys.stdout.flush()
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
