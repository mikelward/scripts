#!/usr/bin/env python3
# script to add/update a Host alias block in .ssh/config
import sys
import os
import argparse
import shutil

def update_ssh_config(config_path, alias, fqdn, username):
    """
    Updates the SSH config file by removing existing blocks for the alias
    and appending a new one.
    """
    if not os.path.exists(config_path):
        lines = []
    else:
        with open(config_path, 'r') as f:
            lines = f.readlines()

    new_lines = []
    skip_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('Host '):
            # Extract hosts following 'Host'.
            hosts = stripped[5:].split()
            if alias in hosts:
                skip_block = True
                continue
            else:
                skip_block = False

        if skip_block:
            continue

        new_lines.append(line)

    # Clean up trailing empty lines to avoid compounding them.
    while new_lines and new_lines[-1].strip() == '':
        new_lines.pop()

    # Add spacing if there are already entries.
    if new_lines:
        new_lines.append('\n')

    # Append new Host block.
    new_block = [
        f"Host {alias} {fqdn}\n",
        f"  User {username}\n",
        f"  HostName {fqdn}\n"
    ]
    new_lines.extend(new_block)

    # Write atomically.
    temp_path = config_path + '.tmp'
    try:
        with open(temp_path, 'w') as f:
            f.writelines(new_lines)
        os.rename(temp_path, config_path)
        return True
    except Exception as e:
        print(f"Error writing to {config_path}: {e}", file=sys.stderr)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def main():
    parser = argparse.ArgumentParser(description='Update SSH config safely')
    parser.add_argument('alias', help='Alias for the host')
    parser.add_argument('fqdn', help='FQDN for the host')
    parser.add_argument('username', help='Username for the host')
    parser.add_argument('--config', default=os.path.expanduser('~/.ssh/config'), help='Path to SSH config file')
    parser.add_argument('--backup', action='store_true', help='Backup before update')

    args = parser.parse_args()

    if args.backup and os.path.exists(args.config):
        backup_path = args.config + '.bak'
        try:
            shutil.copy2(args.config, backup_path)
            print(f"Backed up {args.config} to {backup_path}")
        except Exception as e:
            print(f"Failed to backup {args.config}: {e}", file=sys.stderr)
            sys.exit(1)

    if update_ssh_config(args.config, args.alias, args.fqdn, args.username):
        print(f"Updated {args.config} with {args.alias} -> {args.fqdn} ({args.username})")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
