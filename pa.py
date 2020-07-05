#!/usr/bin/env python3
# Prints the name of the PulseAudio default sink's active port.

import re
import subprocess

result = subprocess.run(['pacmd', 'list-sinks'], capture_output=True)

port_names = {}
default = False
ports = False
port_re = re.compile(b'^\t\t(\S+): (.*) \(.*\)$')
for line in result.stdout.splitlines():
    if line.startswith(b'  * index: '):
        default = True
    if line.startswith(b'    index: '):
        default = False
    if not default:
        continue
    if line.startswith(b'	ports:'):
        ports = True
    if line.startswith(b'	active port: '):
        active_port = line.split(b':', 1)[1].strip().strip(b'<>')
        print(port_names[active_port].decode('utf-8'))
        ports = False
    if not ports:
        continue
    if m := port_re.match(line):
        port_names[m[1]] = m[2]





