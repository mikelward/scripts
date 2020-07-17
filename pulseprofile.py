#!/usr/bin/env python3
# Prints the name of the PulseAudio default sink's active port and the default
# source's active port.

import argparse
import logging
import re
import subprocess
import sys


logger = logging.getLogger(__name__)


def get_active_card_index(output):
    default = False
    for line in output.splitlines():
        if line.startswith(b'  * index: '):
            default = True
        if line.startswith(b'    index: '):
            default = False
        if not default:
            continue
        if line.startswith(b'	card: '):
            card = int(line.split(b':', 1)[1].strip().split()[0])
            return card

def next_profile(output, card_index):
    in_card = False
    in_profiles = False
    profiles = []
    profile_nums = {}
    profile_num = 0
    want = b'    index: %d' % card_index
    for line in output.splitlines():
        if line.startswith(want):
            in_card = True
        elif line.startswith(b'    index: '):
            in_card = False
        if not in_card:
            continue
        if line == (b'\tprofiles:'):
            in_profiles = True
            continue
        if line.startswith(b'\tactive profile:'):
            in_profiles = False
            active_profile = line.split(b':', 1)[1].strip().strip(b'<>')
            logger.debug('active profile = %s', active_profile)
            active_index = profile_nums[active_profile]
            next_index = active_index + 1
            if next_index >= len(profiles):
                next_index = 0
            return profiles[next_index]
        if not in_profiles:
            continue
        profile = get_profile_name(line)
        if profile == b'off':
            continue
        profiles.append(profile)
        profile_nums[profile] = profile_num
        profile_num += 1


def get_profile_name(rest):
        return rest.split(b' ', 1)[0].strip().rstrip(b':')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    sinks = subprocess.run(['pacmd', 'list-sinks'], capture_output=True)
    card_index = get_active_card_index(sinks.stdout)
    cards = subprocess.run(['pacmd', 'list-cards'], capture_output=True)
    profile = next_profile(cards.stdout, card_index)
    logger.info('Setting profile to %s', profile)
    subprocess.run(['pacmd', 'set-card-profile', str(card_index), profile])


if __name__ == '__main__':
  main()
