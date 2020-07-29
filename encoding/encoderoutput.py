#!/usr/bin/python3

import sys
import threading
import queue
import configparser
import http.server

class SocketWriter(threading.Thread):
    def __init__(self, writerQ, sock, thread_control):
        threading.Thread.__init__(self)
        self.writerQ = writerQ
        self.thread_control = thread_control
        self.sock = sock
        print("initialized Socket Writer")

    def run(self):
        while not self.thread_control['exit_flag']:
            itm = self.writerQ.get()
            if itm != b'00':
                try:
                    self.sock.send(itm)
                except:
                    print(sys.exc_info()[1])
                    self.thread_control['exit_flag'] = 1
        print("Writer exiting...")

class EncoderHTTPServer(http.server.HTTPServer):
    def __init__(self, server_address, global_config, ReaderClass, EncoderClass):
        http.server.HTTPServer.__init__(self, server_address, HTTPDRequestHandler)
        self.global_config = global_config
        self.ReaderClass = ReaderClass
        self.EncoderClass = EncoderClass

class HTTPDRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(s):

        encoderQueue = queue.Queue()
        writerQueue = queue.Queue()
        thread_control = {'exit_flag': 0}
        global_config = s.server.global_config

        readerThread = s.server.ReaderClass(global_config, encoderQueue, thread_control)
        encoderThread = s.server.EncoderClass(global_config, encoderQueue, writerQueue, thread_control)
        writerThread = SocketWriter(writerQueue, s.request, thread_control)

        content_type_map = {'mp3': 'audio/mpeg',
                            'passthrough': 'audio/pcm'
                           }
        encoding_type = global_config.get('encoding', 'type')
        if encoding_type in content_type_map:
            s.send_response(200)
            s.send_header("Content-type", "audio/mpeg")
            s.end_headers()
        else:
            s.send_response(500, "Unknown encoding type %s" % encoding_type)
            return

        writerThread.start()
        encoderThread.start()
        readerThread.start()
        sys.stdout.flush()

        writerThread.join()
        encoderThread.join()
        readerThread.join()

        print("All threads closed")
        sys.stdout.flush()
