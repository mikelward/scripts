#!/usr/bin/env python3
# Prints the name of the PulseAudio default sink's active port and the default
# source's active port.

import re
import subprocess
import sys


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
          # Fall back to the raw port id if it wasn't seen in the ports list.
          return port_names.get(active_port, active_port).decode('utf-8')
      if not ports:
          continue
      if m := port_re.match(line):
          port_names[m[1]] = m[2]


def format_ports(ports):
  # Drop missing ports (no default sink/source, PulseAudio not running)
  # instead of rendering the literal string "None" in the status bar.
  return ' '.join(p for p in ports if p)


def main():
  try:
    results = [subprocess.run(['pacmd', subcommand], capture_output=True)
               for subcommand in ['list-sinks', 'list-sources']]
  except FileNotFoundError:
    print('pa.py: pacmd not found', file=sys.stderr)
    return 1
  print(format_ports(get_active_port(result.stdout) for result in results))
  return 0


if __name__ == '__main__':
  sys.exit(main())
