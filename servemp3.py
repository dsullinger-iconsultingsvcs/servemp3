#!/usr/bin/python3

import sys
import os.path
import configparser
import encoding.encoderinput
import encoding.encoder
import encoding.encoderoutput

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

if __name__ == '__main__':

    ReaderClass = encoding.encoderinput.SoundCardReader

    if 'encoding' in global_config:
        encoder_classes = {'mp3': encoding.encoder.MP3Encoder,
                           'passthrough': encoding.encoder.PassthruEncoder
                          }
        encoding_type = global_config.get('encoding', 'type')
        EncoderClass = encoder_classes[encoding_type]

    else:
        print("encoding not specified, defaulting to mp3")
        EncoderClass = encoding.encoder.MP3Encoder
        global_config.add_section('encoding')
        global_config.set('encoding','type','mp3')

    output_type = 'httpd'
    if 'output' in global_config:
        output_config = global_config['output']
        output_type = output_config.get('type', output_type)

    if output_type == 'httpd':
        port = 8080
        port = output_config.getint('port', port)
        with encoding.encoderoutput.HTTPServerEncoder(("", port), global_config, ReaderClass, EncoderClass) as httpd:
            try:
                print("Listening on port %d" % port)
                sys.stdout.flush()
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            httpd.server_close()

    if output_type == 'file':
        file_output = encoding.encoderoutput.FileOutputEncoder(global_config, 
                      ReaderClass, EncoderClass)
        try:
            sys.stdout.flush()
            file_output.process_stream()
        except KeyboardInterrupt:
            pass
