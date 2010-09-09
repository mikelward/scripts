#!/bin/bash
# allow non-.deb version of Java from Sun to be managed by Debian's alteratives system
# so that we can also install .deb versions on the same system
# Mikel Ward <mikel@mikelward.com>

###
# default values for options
#
basedir=

priority=10

subdirs="bin man"
bindir=/usr/bin
mandir=/usr/share/man
dirmap="bin=$bindir:man=$mandir"

debug=false
simulate=false
verbose=false

###
# functions for error handling, usage, and command line option handling
#
debug()
{
	$debug && echo "$*" >&2
}

error()
{
	echo "$*" >&2
}

info()
{
	$verbose && echo "$*" >&2
}

notice()
{
	echo "$*" >&2
}

run()
{
	if $simulate || $debug; then
		# IFS is used to preserve newlines in --slaves output
		OIFS=$IFS
		IFS=
		echo "$@" >&2
		IFS=$OIFS
	fi
	if ! $simulate; then
		"$@"
	fi
}

usage()
{
	cat <<EOF >&2
Usage: java-alternatives.sh [-dhnv] [-p <priority>] [<java root>]
Example: java-alternatives.sh /usr/jdk1.5.0_22
EOF
}

###
# process the command line
#
while getopts ":dhnp:v" opt
do
	case $opt in
	d)
		debug=true
		;;
	h)
		usage
		exit 0
		;;
	n)
		simulate=true
		;;
	p)
		priority=$OPTARG
		;;
	v)
		verbose=true
		;;
	':')
		echo "Missing argument to -$opt" 1>&2
		usage
		exit 2
		;;
	'?')
		echo "Invalid option -$opt" 1>&2
		usage
		exit 2
		;;
	*)
		echo "Program does not support -$opt yet" 1>&2
		usage
		exit 2
		;;
	esac
done
shift $((OPTIND - 1))

basedir=$1
if test -z "$basedir"; then
	error "No Java root directory specified"
	usage
	exit 2
fi
debug "basedir is $basedir"

names=

###
# common array handling functions
#

# add_to_array <array name> <value>
# this is not very efficient for large arrays
# uses newlines to separate entries to allow for storing file names containing spaces
add_to_array()
{
	OIFS=$IFS
	IFS='
'

	local array=$1
	local value=$2
	
	eval $array="\${$array:+\$$array
}\$value"

	IFS=$OIFS
}

# in_array <array name> <value>
in_array()
{
	OIFS=$IFS
	IFS='
'

	local array=$1
	local value=$2
	local found=0
	
	for element in ${!array}; do
		if test "$element" = "$value"; then
			found=1
			break
		fi
	done

	IFS=$OIFS
	if test $found -eq 1; then
		return 0
	else
		return 1
	fi
}

###
# functions for this program
#

# determine where the symlink should be,
# e.g. for /usr/jdk1.5.0_22/bin/java return /usr/bin/java
get_destination_path()
{
	local base=$1
	local path=$2
	local dirmap=$3

	# strip any trailing slash for consistency
	base=${base%/}
	if test "$base" = ""; then
		error "Cannot determine directory for $path: root directory?"
		return 1
	fi

	local subdir=${path#$base}
	if test "$subdir" = "$path"; then
		error "Cannot determine subdirectory for $path"
		return 1
	fi
	subdir=${subdir#/}
	if test "$subdir" = ""; then
		error "Unexpected empty directory: root directory?"
		return 1
	fi
	subdir=${subdir%%/*}
	if test "$subdir" = ""; then
		error "Unexpected empty directory: //?"
		return 1
	fi

	dirmap=$(get_mapped_directory $subdir $dirmap)

	if test $? -eq 0 -a -n "$dirmap"; then
		local dest
		dest=${path#$base}
		dest=${dest#/$subdir}
		dest=$dirmap$dest
		echo $dest
		return 0
	else
		error "Cannot get target directory for $path"
		return 1
	fi
}

# given a bare subdirectory,
# return where files from that subdirectory
# should be installed
# e.g. "bin" => "/usr/bin"
# at the moment, it only works for an exact match on the first pathname component
# this may change later
get_mapped_directory()
{
	local subdir=$1
	local dirmap=$2
	local result=

	OIFS=$IFS
	IFS=:

	debug "Getting mapped directory for $subdir"

	local dir
	for dir in $dirmap; do
		local key
		key=${dir%%=*}
		if test "$key" = "$dir"; then
			error "Skipping invalid dirmap entry $dir"
			continue
		fi
		if test "$subdir" = "$key"; then
			local val
			val=${dir#$key=}
			if test "$val" = "$dir"; then
				error "Skipping invalid dirmap entry $dir with key=$key"
				continue
			else
				debug "$subdir -> $val"
				result=$val
				break
			fi
		fi
	done

	IFS=$OIFS

	if test -n "$result"; then
		echo $result
		return 0
	else
		notice "Missing dirmap for $subdir"
		return 1
	fi
}


###
# main
#

# determine where each file (program, man page, etc.)
# should be installed to and build the command line args to
# update-alternatives --install...
files=$(for subdir in $subdirs; do find $basedir/$subdir -type f -print; done)
for file in $files; do
  
	# We might get /usr/java/share/man/man1/java.1 and
	# /usr/java/share/man/ja_JP.eucJP/man1/java.1.
	# We can only have one or the other, because both would
	# be called /etc/alternatives/java.1.
	# There's no guarantee these are passed to us in any given order,
	# so naively skip anything that doesn't look like a default
	# man page.
	case $file in */man/*)
		case $file in */man/man*)
			# keep default locale man pages
			:
			;;
		*)
			info "Skipping $file: prefer default locale man pages"
			continue
			;;
		esac
		;;
	esac


	name=${file##*/}
	if test "$name" = "$file"; then
		error "Cannot determine filename for $file"
		continue
	fi
	dest=$(get_destination_path $basedir $file $dirmap)
	if test -z "$dest"; then
		error "Cannot determine target for $file"
		continue
	fi


	if ! in_array names $name; then
		add_to_array names $name

		case $file in */bin/java)
			# the main java program should be specified via --install
			install="    --install $dest $name $file"
			;;
		*)
			# the other files are specified via --slave
			# weird spacing is to make it line up with --install line in output
			slaves="$slaves
    --slave   $dest $name $file"
			;;
		esac
	else	
		notice "Skipping $file: already in use"
	fi
done

# TODO: bin/java should honor $dirmap too
# $slaves already has a newline before it, so don't add one here too
if $simulate; then
	echo "/usr/sbin/update-alternatives 
$install $priority $slaves"
else
	run sudo /usr/sbin/update-alternatives \
$install $priority $slaves
fi
