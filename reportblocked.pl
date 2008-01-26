#!/usr/bin/perl
# report which mail messages were rejected during sending in the most recent mail log file
# $Id$

use strict;
use warnings;

# Jul  4 09:02:37 eagle postfix/smtpd[10848]: NOQUEUE: reject: RCPT from mailhost.terra.es[213.4.149.12]: 450 4.7.1 <csmtpout1.frontal.correo>: Helo command rejected: Host not found; from=<leticia_info3@terra.es> to=<michael@endbracket.net> proto=ESMTP helo=<csmtpout1.frontal.correo>
#grep 'NOQUEUE: reject: RCPT from [^ ]*: 5..' /var/log/mail | sed -e 's/^.*RCPT from \([^\[]*\)\[\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)\]: \([0-9][0-9][0-9]\).*from=<\([^ ]*\)>.*/\4 (\1)/'

#my @users = ("michael", "mikel");
my @users = ("mikel");
my $domain = "endbracket.net";
my $postmaster = undef;
my $maillog;
if (@ARGV >= 1)
{
	$maillog = $ARGV[0];
}
else
{
	$maillog = "/var/log/mail";
}
#my $maillog = "/home/michael/maillog";
my $sendmail = "/usr/lib/sendmail";

sub print_html_header
{
	print SENDMAIL "<html>\n";
	print SENDMAIL "<head>\n";
	print SENDMAIL "<style type=\"text/css\">\n";
	print SENDMAIL "body { font-family: sans-serif }\n";
	print SENDMAIL "td { white-space: nowrap }\n";
	print SENDMAIL "</style>\n";
	print SENDMAIL "<body>\n";
	print SENDMAIL "<p>Somebody tried to send you the following messages, but they were blocked because they looked suspicious.</p>\n";
	print SENDMAIL "<p>In each case, the person who sent the message will have received an error message informing them the message was not delivered.</p>\n";
	print SENDMAIL "<p>If you wanted one of these messages, please contact the person who sent it.  They will need to ask their system administrator to fix the problem mentioned in the Reason column and then re-send the message.</p>\n";
	#print SENDMAIL "<p>If you have any questions, please <a href=\"mailto:$postmaster\">contact the post master.</a></p>\n";
	print SENDMAIL "<table>\n";
	print SENDMAIL "<tr align=\"left\">\n";
	print SENDMAIL "<th>Time</th><th>From</th><th>Country</th><th>Reason</th>\n";
	print SENDMAIL "</tr>\n";
}

sub print_text_header
{
	print SENDMAIL "Somebody tried to send you the following messages, but they were blocked because they looked suspicious.\n\n";
	print SENDMAIL "In each case, the person who sent the message will have received an error message informing them the message was not delivered.\n\n";
	print SENDMAIL "If you wanted one of these messages, please contact the person who sent it.  They will need to ask their system administrator to fix the problem mentioned in the Reason column and then re-send the message.\n\n";
	#print SENDMAIL "<p>If you have any questions, please <a href=\"mailto:$postmaster\">contact the post master.</a></p>\n";
	printf SENDMAIL "%-7s  %-33s  %-14s  %-19s\n", "TIME", "FROM", "COUNTRY", "REASON";
}

sub print_html_body
{
	my($recordref) = shift(@_);
	my(%record) = %$recordref;

	print SENDMAIL "<tr>\n";
	print SENDMAIL "<td>$record{time}</td>\n";
	print SENDMAIL "<td><a href=\"mailto:$record{from}\">$record{from}</a></td>\n";
	print SENDMAIL "<td>$record{country}</td>\n";
	#print SENDMAIL "<td>$record{host}</td>\n";
	print SENDMAIL "<td>$record{reason}</td>\n";
	#print SENDMAIL "<td>$record{details}</td>\n";
	print SENDMAIL "</tr>\n";
}

sub print_text_body
{
	my($recordref) = shift(@_);
	my(%record) = %$recordref;

	printf SENDMAIL "%-7s  %-33s  %-14s  %-19s\n", $record{time}, $record{from}, $record{country}, $record{reason};
}

sub print_html_footer
{
	my($statsref) = shift(@_);
	my(%stats) = %$statsref;

	print SENDMAIL "</table>\n";

	if ($stats{blocked} == 0)
	{
		print SENDMAIL "<p>No messages blocked</p>\n";
	}
	elsif ($stats{blocked} == 1)
	{
		print SENDMAIL "<p>One message blocked</p>\n";
	}
	else
	{
		print SENDMAIL "<p>$stats{blocked} messages blocked</p>\n";
	}

	if ($stats{delivered} == 0)
	{
		print SENDMAIL "<p>No messages delivered</p>\n";
	}
	elsif ($stats{delivered} == 1)
	{
		print SENDMAIL "<p>One message delivered</p>\n";
	}
	else
	{
		print SENDMAIL "<p>$stats{delivered} messages delivered</p>\n";
	}

	if (open(TIMEZONE, "/etc/timezone"))
	{
		my $timezone = <TIMEZONE>;
		chomp $timezone;

		my ($continent, $city) = split('/', $timezone);
		$city =~ s/_/ /g;
		my $offset = `env TZ=$timezone date '+%z'`;
		chomp $offset;

		print SENDMAIL "<p>Times given are in $city time (UTC$offset)</p>\n";
	}

	print SENDMAIL "</body>\n";
	print SENDMAIL "</html>\n";
}

sub print_text_footer
{
	my($statsref) = shift(@_);
	my(%stats) = %$statsref;

	print SENDMAIL "\n";

	if ($stats{blocked} == 0)
	{
		print SENDMAIL "No messages blocked\n\n";
	}
	elsif ($stats{blocked} == 1)
	{
		print SENDMAIL "One message blocked\n\n";
	}
	else
	{
		print SENDMAIL "$stats{blocked} messages blocked\n\n";
	}

	if ($stats{delivered} == 0)
	{
		print SENDMAIL "No messages delivered\n\n";
	}
	elsif ($stats{delivered} == 1)
	{
		print SENDMAIL "One message delivered\n\n";
	}
	else
	{
		print SENDMAIL "$stats{delivered} messages delivered\n\n";
	}

	if (open(TIMEZONE, "/etc/timezone"))
	{
		my $timezone = <TIMEZONE>;
		chomp $timezone;

		my ($continent, $city) = split('/', $timezone);
		$city =~ s/_/ /g;
		my $offset = `env TZ=$timezone date +%z`;
		chomp $offset;

		print SENDMAIL "Times given are in $city time (UTC$offset)\n\n";
	}
}

USER:
foreach my $user (@users)
{
	my @records;

	open(MAILLOG, "<$maillog")
		or die "Cannot open $maillog";

	my($blocked) = 0;
	my($delivered) = 0;
	while (<MAILLOG>)
	{
		my $line = $_;
		chomp $line;

		if ($line =~ m#^(...) (..) (........) \S+ postfix/(smtpd|cleanup).*reject.*to=<($user(?:\+[^@]*)?@.*)>#)
		{
			my $month = $1;
			my $day = $2;
			my $time = $3;
			my $server = $4;

			my $host;
			my $addr;
			my $exterror;
			my $reason;
			my $from;
			my $to;
			my $helo;
			my $error;
			my $details;

			my $hours;
			my $minutes;
			my $seconds;
			if ($time =~ /^(..):(..):(..)$/)
			{
				$hours = $1 + 0;
				$minutes = $2;
				$seconds = $3;
			}

			# convert to 12-hour time
			my $timesuffix;
			if ($hours == 0)
			{
				$hours = 12;
				$timesuffix = "am";
			}
			elsif ($hours == 12)
			{
				$timesuffix = "pm";
			}
			elsif ($hours > 12)
			{
				$hours -= 12;
				$timesuffix = "pm";
			}
			else
			{
				$timesuffix = "am";
			}
			$time = "$hours:$minutes$timesuffix";

			# Jan 16 04:28:20 falcon postfix/smtpd[27385]: NOQUEUE: reject: RCPT from unknown[88.233.24.124]: 550 5.7.1 Client host rejected: cannot find your hostname, [88.233.24.124]; from=<info_1@spor-haberleri.com> to=<michael@endbracket.net> proto=SMTP helo=<spor-haberleri1470.com>
			if ($line =~ m#^.*postfix/smtpd\[\d+\]: NOQUEUE: reject: RCPT from ([^[]*)\[([^]]*)\]: (5\d+) (\S+) (.*); from=<([^>]*)> to=<($user(?:\+[^@]*)?@.*)> proto=[^ ]* helo=<(.*)>#i)
			{
				$blocked++;

				$host = $1;
				$addr = $2;
				$error = $3;
				$exterror = $4;
				$reason = $5;
				$from = $6;
				$to = $7;
				$helo = $8;

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
					elsif ($blacklist =~ /spam\.tqmcube\.com$/)
					{
						$blacklist = "TQMcube";
					}
					#$reason = "Blacklisted by $blacklist";
					$reason = "Listed by $blacklist";
					$details = $addr;
				}
				elsif ($reason =~ /cannot find your hostname/)
				{
					$reason = "Missing reverse DNS";
					$details = $addr;
				}
				elsif ($reason =~ /Helo command rejected/)
				{
					$reason = "Invalid HELO name";
					$details = $addr;
				}
				elsif ($reason =~ /User unknown in local recipient table/)
				{
					$reason = "Bad To address";
					$details = $to;
				}
				elsif ($reason =~ /Suspected spam/)
				{
					$reason = "Suspected spam";
				}
				# SPF version 1
				elsif ($reason =~ m#Recipient address rejected: Please see http://www.openspf.org#)
				{
					$reason = "Forged From address";
				}
				# SPF version 2 (my message from /usr/lib/postfix/postfix-policyd-spf-perl)
				elsif ($reason =~ m#Forged From address: Please see http://www.openspf.org#)
				{
					$reason = "Forged From address";
				}
				elsif ($reason =~ m#Character set prohibited#)
				{
					$reason = "Foreign character set";
				}
				elsif ($reason =~ /Recipient address rejected: /)
				{
					$reason =~ s/^.*Recipient address rejected: //;
				}

				# give bounce messages a more meaningful name
				# (however the address isn't technically the same)
				if ($from =~ /^$/)
				{
					$from = "postmaster\@$host";
				}
			}
			# Jan 16 16:09:37 falcon postfix/cleanup[29790]: A6E4F22800B: reject: header Content-Type: text/plain;??charset="gb2312" from poplet2.per.eftel.com[203.24.100.45]; from=<cplwest@cpl.net.au> to=<mikel@mikelward.com> proto=ESMTP helo=<poplet2.per.eftel.com>: 5.7.1 554 Character set prohibited.  You have sent a message in a language I don't understand.  Please see http://endbracket.net/help/spam/foreign for more information.
			elsif ($line =~ m#^.*postfix/cleanup\[\d+\]: \w+: reject: header Content-Type: .*charset="([^"]*)" from ([^[]*)\[([^]]*)\]; from=<([^>]*)> to=<$user(?:\+[^@]*)?@.*> proto=[^ ]* helo=<.*>: 5\.\d+\.\d+ (5\d\d) Character set prohibited#i)
			{
				$blocked++;

				$host = $2;
				$addr = $3;
				$from = $4;
				$error = $5;
				$details = $1;

				$reason = "Foreign language";
			}
			# Jan 24 12:33:44 falcon postfix/cleanup[25080]: 615E5228012: reject: header Subject: =?euc-kr?q?Subscription_Update_-_January_23=2C_2008?= from sjl-smtp5.sjl.youtube.com[64.15.123.233]; from=<service@youtube.com> to=<mikel@mikelward.com> proto=ESMTP helo=<sjl-smtp5.sjl.youtube.com>: 5.7.1 554 Character set prohibited.  You have sent a message in a language I don't understand.  Please see http://endbracket.net/help/spam/foreign for more information.
			elsif ($line =~ m#^.*postfix/cleanup\[\d+\]: \w+: reject: header Subject: .*?=\?(.*?)\?.*? from ([^[]*)\[([^]]*)\]; from=<([^>]*)> to=<$user(?:\+[^@]*)?@.*> proto=[^ ]* helo=<.*>: 5\.\d+\.\d+ (5\d\d) Character set prohibited#i)
			{
				$blocked++;

				$host = $2;
				$addr = $3;
				$from = $4;
				$error = $5;
				$details = $1;

				$reason = "Foreign language";
			}
			elsif ($line =~ m#^.*postfix/smtpd\[\d+\]: NOQUEUE: reject_warning: RCPT from ([^[]*)\[([^]]*)\]: (\d+) (\S+) (.*); from=<([^>]*)> to=<($user(?:\+[^@]*)?@.*)> proto=[^ ]* helo=<(.*)>#i)
			{
				# This message wasn't rejected
				next;
			}
			elsif ($line =~ m#^.*postfix/smtpd\[\d+\]: NOQUEUE: reject: RCPT from ([^[]*)\[([^]]*)\]: (4\d+) (\S+) (.*); from=<([^>]*)> to=<($user(?:\+[^@]*)?@.*)> proto=[^ ]* helo=<(.*)>#i)
			{
				# Temporary rejection, don't report on this one
				next;
			}
			else
			{
				print STDERR "No rule for $line\n";
				# Not a known rejection message
			}

			my $country = `geoiplookup $addr`;
			chomp($country);
			$country =~ s/^GeoIP Country Edition: //;
			$country =~ s/^.*?, //;	# strip country code
			$country =~ s/,.*$//;	# strip things like "Republic of"

				#my %record;
			my $recordref = { time => $time, from => $from, country => $country, host => $host, reason => $reason, details => $details };
			#$record{time} = $time;
			#$record{from} = $from;
			#$record{country} = $country;
			#$record{host} = $host;
			#$record{reason} = $reason;
			#$record{details} = $details;

			#push @records, %record;
			push @records, $recordref;

		}
		# Jul  6 06:33:21 eagle postfix/local[11666]: 5030B3746C: to=<michael@endbracket.net>, relay=local, delay=6.6, delays=3.1/0.04/0/3.5, dsn=2.0.0, status=sent (delivered to command: /usr/local/bin/procmail -p -a "$EXTENSION")
		elsif (m#^(...) (..) (........) ([^ ]*) postfix/local\[\d+\]:.*to=<($user(?:\+[^@]*)?@.*)>.*status=sent#)
		{
			$delivered++;
		}
	}

	if ($delivered == 0 && $blocked == 0)
	{
		next USER;
	}

	my $statsref = { blocked => $blocked, delivered => $delivered };

	open(SENDMAIL, "|$sendmail -t")
		or die "Cannot open sendmail pipe";

	print SENDMAIL "To: $user\@$domain\n";
	if (defined $postmaster)
	{
		print SENDMAIL "Bcc: $postmaster\n";
	}

	print SENDMAIL "Subject: Blocked Messages Report for $user\n";
	print SENDMAIL "MIME-Version: 1.0\n";
	print SENDMAIL "Content-Type: multipart/alternative; boundary=\"boundary\"\n";
	print SENDMAIL "\n";
	print SENDMAIL "This is a multi-part message in MIME format.\n";

	print SENDMAIL "--boundary\n";
	print SENDMAIL "Content-Type: text/plain\n";
	print SENDMAIL "\n";


	print_text_header();

	foreach my $recordref (@records)
	{
		print_text_body($recordref);
	}

	print_text_footer($statsref);


	print SENDMAIL "--boundary\n";
	print SENDMAIL "Content-Type: text/html\n";
	print SENDMAIL "\n";

	print_html_header();

	foreach my $recordref (@records)
	{
		print_html_body($recordref);
	}

	print_html_footer($statsref);

	print SENDMAIL "--boundary--\n";

	close(SENDMAIL);
}

#sed -e 's/^.*RCPT from \([^\[]*\)\[\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)\]: \([0-9][0-9][0-9]\).*from=<\([^ ]*\)>.*/\4 (\1)/'
