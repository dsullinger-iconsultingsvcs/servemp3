#!/usr/bin/python3

import sys
import threading
import queue
import configparser
import http.server
import time

class SocketWriter(threading.Thread):
    def __init__(self, writerQ, sock, thread_control):
        threading.Thread.__init__(self)
        self.writerQ = writerQ
        self.thread_control = thread_control
        self.sock = sock
        print("initialized Socket Writer")

    def run(self):
        item_count = 0
        while not self.thread_control['exit_flag']:
            itm = self.writerQ.get()
            item_count = item_count + 1
            if item_count > 100:
                item_count = 0
                queue_size = self.writerQ.qsize()
                if queue_size > 1:
                    print("!!!Queue size is %d" % queue_size)
                sys.stdout.flush()
            if itm != b'00':
                try:
                    self.sock.send(itm)
                except:
                    print(sys.exc_info()[1])
                    self.thread_control['exit_flag'] = 1
        print("Writer exiting...")

class FileWriter(threading.Thread):
    def __init__(self, config, writerQ, thread_control):
        threading.Thread.__init__(self)
        self.writerQ = writerQ
        self.thread_control = thread_control
        self.FILENAME = str(time.time())
        if 'output' in config:
            self.FILENAME = config['output'].get('Filename', self.FILENAME)
        print(f'initialized FileWriter ({self.FILENAME})')

    def run(self):
        out_file = open(self.FILENAME, "wb")
        while not self.thread_control['exit_flag']:
            itm = self.writerQ.get()
            if itm != b'00':
                try:
                    out_file.write(itm)
                except:
                    print(sys.exc_info()[1])
                    self.thread_control['exit_flag'] = 1
        print("FileWriter exiting...")
        out_file.close()

class FileOutputEncoder:
    def __init__(self, global_config, ReaderClass, EncoderClass):
        self.global_config = global_config
        self.ReaderClass = ReaderClass
        self.EncoderClass = EncoderClass

    def process_stream(self):
        encoder_queue = queue.Queue()
        writer_queue = queue.Queue()
        thread_control = {'exit_flag': 0}
        global_config = self.global_config
        reader_thread = self.ReaderClass(global_config, encoder_queue, thread_control)
        encoder_thread = self.EncoderClass(global_config, encoder_queue, writer_queue, thread_control)
        writer_thread = FileWriter(global_config, writer_queue, thread_control)

        writer_thread.start()
        encoder_thread.start()
        reader_thread.start()
        sys.stdout.flush()

        writer_thread.join()
        encoder_thread.join()
        reader_thread.join()

        print("All threads closed")
        sys.stdout.flush()


class HTTPServerEncoder(http.server.HTTPServer):
    def __init__(self, server_address, global_config, ReaderClass, EncoderClass):
        http.server.HTTPServer.__init__(self, server_address, HTTPDRequestHandler)
        self.global_config = global_config
        self.ReaderClass = ReaderClass
        self.EncoderClass = EncoderClass

class HTTPDRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(s):

        encoder_queue = queue.Queue()
        writer_queue = queue.Queue()
        thread_control = {'exit_flag': 0}
        global_config = s.server.global_config

        reader_thread = s.server.ReaderClass(global_config, encoder_queue, thread_control)
        encoder_thread = s.server.EncoderClass(global_config, encoder_queue, writer_queue, thread_control)
        writer_thread = SocketWriter(writer_queue, s.request, thread_control)

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

        writer_thread.start()
        encoder_thread.start()
        reader_thread.start()
        sys.stdout.flush()

        writer_thread.join()
        encoder_thread.join()
        reader_thread.join()

        print("All threads closed")
        sys.stdout.flush()
