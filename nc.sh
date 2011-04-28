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
Usage: $scriptname [-h] [-t|-u] <host> <port>
EOF
}

scriptname=nc.sh
proto=tcp

while getopts ":htu" option
do
    case $option in
    h)
        usage
        exit 0
        ;;
    t)
        proto=tcp
        ;;
    u)
        proto=udp
        ;;
    ':')
        echo "Missing argument to -$OPTARG" 1>&2
        usage
        exit 2
        ;;
    '?')
        echo "Invalid option -$OPTARG" 1>&2
        usage
        exit 2
        ;;
    *)
        echo "The -$option option is not supported yet" 1>&2
        usage
        exit 2
        ;;
    esac
done
shift $((OPTIND - 1))

if test $# -ne 2; then
    usage
    exit 2
fi

case $proto in
tcp|udp)
    ;;
*)
    echo "Invalid protocol $proto" 1>&2
    exit 3
    ;;
esac

host=$1
port=$2

# {sd}<>file opens file for reading and writing,
# setting sd to the file descriptor number the shell chose
# /dev/proto/host/port is a bash feature to provide TCP/UDP
# socket access
if exec {sd}<>/dev/$proto/$host/$port; then
    :
else
    echo "Error connecting to $host:$port via $proto" 1>&2
    exit 1
fi
# try to read from the server first, in case it already has stuff to send...
# (e.g. daytime, chargen, etc.)
sleep 0.01
while read -t 0 -u $sd dummy; do
    if read -u $sd recvdata; then
        echo "$recvdata"
    else
        # assume EOF
        exit 0
    fi
done
# read a line of input from stdin...
while read senddata; do
    echo "$senddata" 1>&$sd
    # process as many lines of data as the server sends back...
    while read -t 0 -u $sd dummy; do
        # read -t 0 doesn't seem to modify dummy, nor does it handle EOF
        # so we call regular read now we know it won't block...
        if read -u $sd recvdata; then
            echo "$recvdata"
        else
            # assume EOF
            exit 0
        fi
    done
done

# vim: set ts=4 sw=4 tw=0 et:
