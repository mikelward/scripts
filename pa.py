#!/usr/bin/env python3
# Prints the name of the PulseAudio default sink's active port and the default
# source's active port.

import re
import subprocess


def get_active_port(output):
  port_names = {}
  default = False
  ports = False
  port_re = re.compile(b'^\t\t(\S+): (.*) \(.*\)$')
  for line in output.splitlines():
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
          return port_names[active_port].decode('utf-8')
      if not ports:
          continue
      if m := port_re.match(line):
          port_names[m[1]] = m[2]


def main():
  ports = [get_active_port(result.stdout)
           for subcommand in ['list-sinks', 'list-sources']
           for result in [subprocess.run(['pacmd', subcommand], capture_output=True)]]
  print(' '.join('%s' % p for p in ports))


if __name__ == '__main__':
  main()
