#servemp3
Python process to stream MP3 captured from a sound card

This Python 3 program is used to encode sound data from a sound card to MP3 data, then stream the MP3 data over HTTP to a client.


Note that servemp3.py uses http.server and comes with all the associated security considerations for using that module.

Prerequisites: pyaudio, lameenc

To use:
- Install the prerequisite Python 3 packages
- Set up the configuration (.config) file with the options for server port, reading from the sound card, and LAME encoding.  You can then run the install.sh script to copy the program to /usr/local/bin and the config to /etc
- The install.sh script will also set up the systemd service.  You will need to ensure the prerequisite packages are installed for the system (not the user level).
- Run **servemp3.py [config]** where [config] is the name of a configuration file.  If you exclude the configuration file and a default is not found in /etc, then default values will be set for you.

See the pyaudio and lameenc documentation for potential configuration values, and keep in mind that not all configuration options have been implemented or are available through configuration.


