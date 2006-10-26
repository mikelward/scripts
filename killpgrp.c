/*
 * $Id$
 *
 * Kills all processes belonging to the supplied process group id.
 *
 * In the normal case, this allows you to kill a process and any of its
 * children.
 */

#include <sys/types.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

void usage()
{
    fprintf(stderr, "Usage: killpgrp <pgid>\n");
}

int main(int argc, char **argv)
{
    int pgid;

    if (argc < 2) {
        usage();
        exit(2);
    }

    pgid = atoi(argv[1]);
    pgid = -pgid;
    kill(pgid, SIGTERM);

    exit(0);
}
