#!/usr/bin/perl
#
# $Id$

# report which mail messages were rejected during sending in the most recent mail log file

# Jul  4 09:02:37 eagle postfix/smtpd[10848]: NOQUEUE: reject: RCPT from mailhost.terra.es[213.4.149.12]: 450 4.7.1 <csmtpout1.frontal.correo>: Helo command rejected: Host not found; from=<leticia_info3@terra.es> to=<michael@endbracket.net> proto=ESMTP helo=<csmtpout1.frontal.correo>
#grep 'NOQUEUE: reject: RCPT from [^ ]*: 5..' /var/log/mail | sed -e 's/^.*RCPT from \([^\[]*\)\[\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)\]: \([0-9][0-9][0-9]\).*from=<\([^ ]*\)>.*/\4 (\1)/'

open(MAILLOG, "</var/log/mail")
  or die "Cannot open mail log";

print "To: postmaster\@endbracket.net\n";
print "Subject: Blocked Messages Report\n";
print "MIME-Version: 1.0\n";
print "Content-Type: text/html\n";
print "\n";

print "<html>\n";
print "<body>\n";
print "<table>\n";
print "<tr align=\"left\">\n";
print "<th>Time</th><th>From</th><th>Country</th><th>Reason</th>\n";
print "</tr>\n";
while (<MAILLOG>)
{
	#if (m#postfix/smtpd\[\d+\]: NOQUEUE: reject: RCPT from ([^[]*)\[([^]]*)\]: (5..) ([^ ]*) (.*); from=<([^>]*)> to=<([^>]*) proto=[^ ]* helo=(.*)#)
	if (m#^(...) (..) (........) ([^ ]*) postfix/smtpd\[\d+\]: NOQUEUE: reject: RCPT from ([^[]*)\[([^]]*)\]: (5..) ([^ ]*) (.*); from=<([^>]*)> to=<([^>]*)> proto=[^ ]* helo=#)
	{
		my $month = $1;
		my $day = $2;
		my $time = $3;
		my $server = $4;

		my $host = $5;
		my $addr = $6;
		my $error = $7;
		my $exterror = $8;
		my $reason = $9;
		my $from = $10;
		my $to = $11;
		my $helo = $12;


		my $hours;
		my $minutes;
		my $seconds;
		if ($time =~ /^(..):(..):(..)$/)
		{
			$hours = $1 + 0;
			$minutes = $2;
			$seconds = $3;
		}

		$time = "$hours:$minutes";

#		my $timesuffix;
#		if ($hours == 12)
#		{
#			$timesuffix = "pm";
#		}
#		elsif ($hours > 12)
#		{
#			$hours -= 12;
#			$timesuffix = "pm";
#		}
#		else
#		{
#			$timesuffix = "am";
#		}
#		$time = "$hours:$minutes $timesuffix";

		#$time =~ s/^0//;		# strip leading zero
		#$time =~ s/...$//;		# strip seconds

		my $country = `geoiplookup $addr`;
		$country =~ s/^GeoIP Country Edition: //;
		$country =~ s/^.*?,//;	# strip country code
		$country =~ s/,.*$//;	# strip things like "Republic of"

		my $details;
		if ($reason =~ /Your mail server is blacklisted by ([^ ]*)\. /)
		{
			my $blacklist = $1;
			if ($blacklist =~ /spamhaus\.org$/)
			{
				$blacklist = "Spamhaus";
			}
			elsif ($blacklist =~ /spamcop\.net$/)
			{
				$blacklist = "Spamcop";
			}
			elsif ($blacklist =~ /psbl\.surriel\.com$/)
			{
				$blacklist = "PSBL";
			}
			elsif ($blacklist =~ /list\.dsbl\.org$/)
			{
				$blacklist = "DSBL";
			}
			elsif ($blacklist =~ /dnsbl\.sorbs\.net$/)
			{
				$blacklist = "SORBS";
			}
			$reason = "Blacklisted by $blacklist";
			$details = $addr;
		}
		elsif ($reason = /cannot find your hostname/)
		{
			$reason = "Missing reverse DNS";
			$details = $addr;
		}
		elsif ($reason = "User unknown in local recipient table")
		{
			$reason = "Bad To address";
			$details = $to;
		}


		print "<tr>\n";
		print "<td>$time</td>\n";
		print "<td>$from</td>\n";
		print "<td>$country</td>\n";
		#print "<td>$host</td>\n";
		print "<td>$reason</td>\n";
		#print "<td>$details</td>\n";
		print "</tr>\n";
	}
}
print "</table>\n";
print "</body>\n";
print "</html>\n";


#sed -e 's/^.*RCPT from \([^\[]*\)\[\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)\]: \([0-9][0-9][0-9]\).*from=<\([^ ]*\)>.*/\4 (\1)/'
