#!/bin/bash
#
# nc.sh
#
# use bash features to provide a simple TCP client similar to nc or telnet
# might be useful on systems where those are not installed by default
# (e.g. some Red Hat EL systems)
#

usage()
{
    cat 1>&2 <<EOF
Usage: nc.sh <host> <port>
EOF
}

if test $# -ne 2; then
    usage
    exit 2
fi

host=$1
port=$2
proto=tcp

exec 3<>/dev/$proto/$host/$port
while true; do
    while read senddata; do
        echo "$senddata" 1>&3
        while read -t 0 -u 3 dummy; do
            if read -u 3 inputdata; then
                echo "$inputdata"
            else
                # assume EOF
                exit 0
            fi
        done
    done
done

