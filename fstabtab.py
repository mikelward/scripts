#!/usr/bin/python
#
# fstabtab.py
# make all the entries in /etc/fstab line up
#
# handling of comment lines is still being decided
#

# longest length item in each field
# e.g. maxfieldlens = {0: 40, 1: 15, 2: 4, 3: 20, 4: 1, 5: 1}
maxfieldlens = {}

fstab = open('/etc/fstab')

lines = fstab.readlines()

for line in lines:
    if line.startswith('#'): continue

    fields = line.split()
    for (fieldno, field) in enumerate(fields):
        if fieldno not in maxfieldlens:
            maxfieldlens[fieldno] = 0
        maxfieldlen = maxfieldlens[fieldno]
        fieldlen = len(field)
        if fieldlen > maxfieldlen:
            maxfieldlens[fieldno] = fieldlen

fields = sorted(maxfieldlens)
fieldlens = [maxfieldlens[field] for field in fields]
def fieldlen_to_format(fieldlen):
    return '%-' + str(fieldlen) + 's'
format = '  '.join(map(fieldlen_to_format, fieldlens))

for line in lines:
    if line.startswith('#'):
        print line,
    else:
        fields = line.split()
        print format % tuple(fields)
