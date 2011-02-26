#!/bin/bash
# print information about a single option or command
# Mikel Ward <mikel@mikelward.com>

# Example Usage:
# opt bash continue
# opt rsync -v

scriptname=desc

usage()
{
    cat <<EOF 1>&2
Usage: $scriptname <command> [<option|section>]
Example:
    $scriptname bash getopts (shows documentation for bash getopts)
    $scriptname ssh -v       (shows documentation for ssh -v flag)
    $scriptname select       (shows SYNOPSIS for select(2))
    $scriptname 'open(2)'    (shows SYNOPSIS for open(2))
EOF
}

if test $# -lt 1; then
    usage
    exit 2
fi

manpage="$1"
option="${2:-SYNOPSIS}"

if [[ "$manpage" =~ (.*)\((.*)\) ]]; then
    manpage=${BASH_REMATCH[1]}
    section=${BASH_REMATCH[2]}
fi

# XXX man calls col when it's part of a pipeline,
# which strips the bold and underline, and breaks
# UTF-8 encoding (try "man bash" for example)
# set LANG=C until a better solution is found
LANG=C man ${section:+-s $section} "$manpage" | perl -n -e "
BEGIN {
    \$option = \"$option\";
    \$inside = 0;
}"'
if (!$inside) {
    if (/^(\s*)\Q$option\E\b/p) {
        # start of this option
        $spaces = $1;
        $inside = 1;
        print;
    }
}
else {
    if (/^$spaces\S/) {
        # start of next option;
        exit;
    }
    elsif (/^\S/) {
        # start of next section
        exit;
    }
    else {
        print;
    }
}
' | "${PAGER:-less}"
