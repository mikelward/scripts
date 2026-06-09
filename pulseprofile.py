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
    for line in output.splitlines():
        # Card headers look like "    index: 1" ("  * index: 1" for the
        # default card). Compare the parsed number, not a string prefix, so
        # card 1 does not match cards 10, 11, ...
        stripped = line.lstrip(b' *')
        if stripped.startswith(b'index: '):
            index = int(stripped.split(b':', 1)[1].strip().split()[0])
            in_card = index == card_index
        if not in_card:
            continue
        if line == (b'\tprofiles:'):
            in_profiles = True
            continue
        if line.startswith(b'\tactive profile:'):
            in_profiles = False
            active_profile = line.split(b':', 1)[1].strip().strip(b'<>')
            logger.debug('active profile = %s', active_profile)
            # The active profile may not be in the dict (e.g. "off" is
            # skipped); fall back to -1 so the next profile is the first one.
            active_index = profile_nums.get(active_profile, -1)
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
    if card_index is None:
        sys.exit('pulseprofile: cannot find the default sink\'s card')
    cards = subprocess.run(['pacmd', 'list-cards'], capture_output=True)
    profile = next_profile(cards.stdout, card_index)
    if profile is None:
        sys.exit('pulseprofile: cannot find a profile for card %d' % card_index)
    logger.info('Setting profile to %s', profile)
    subprocess.run(['pacmd', 'set-card-profile', str(card_index), profile])


if __name__ == '__main__':
  main()
