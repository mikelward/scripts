#!/usr/bin/perl
# vim: set tw=0:

#use strict;
#use warnings;

#my $logfile = "/var/log/apache2/combined.log";
my @logfiles;
if (scalar @ARGV > 0)
{
	@logfiles = @ARGV;
}
else
{
	@logfiles = ("/home/mikelward/logs/mikelward.com/http/access.log.0");
}

foreach my $logfile (@logfiles)
{
	open(LOGFILE, "<$logfile")
		or die "Cannot open log file $logfile\n";

	while (<LOGFILE>)
	{
		chomp;
		#remotehost rfc931 authuser [date] "request" status bytes "referer" "user_agent"
		/([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" (\d+) ([^ ]*) "([^"]*)" "([^"]*)"/;

		my $host = $1;
		my $ident = $2;
		my $user = $3;
		my $date = $4;
		my $request = $5;
		my $status = $6;
		my $bytes = $7;
		my $referrer = $8;
		my $agent = $9;

		my $address = $request;
		$address =~ s/^([A-Z]*) //;
		$address =~ s/ HTTP[^ ]*$//;
		$address =~ s/\?.*//;
		$address =~ s/^\/michael//;

		if (/Opera/)
		{
			$agent =~ s/.*Opera\/(.*?) .*$/Opera $1/;
		}
		elsif ($agent =~ /Safari/)
		{
			$agent =~ s/.*Safari\/(.*?)$/Safari $1/;
		}
		elsif ($agent =~ /(Firefox|BonEcho|Shiretoko|Minefield)/)
		{
			$agent =~ s/.*(?:Firefox|BonEcho|Shiretoko|Minefield)\/(.*?)( .*|$)/Firefox $1/;
		}
		elsif ($agent =~ /Camino/)
		{
			$agent =~ s/.*Camino\/(.*?)$/Camino $1/;
		}
		elsif ($agent =~ /SeaMonkey/)
		{
			$agent =~ s/.*SeaMonkey\/(.*?)$/SeaMonkey $1/;
		}
		elsif ($agent =~ /Netscape/)
		{
			$agent =~ s/.*Netscape\/(.*?)$/Netscape $1/;
		}
		elsif ($agent =~ /Java/)
		{
			$agent =~ s/.*Java\/(.*?)$/Java $1/;
		}
		elsif ($agent =~ /NetFront/)
		{
			$agent =~ s/.*NetFront\/(.*?) .*/NetFront $1/;
		}
		elsif ($agent =~ /Series60/)
		{
			$agent =~ s/.*Series60\/(.*?) .*/Series60 $1/;
		}
		elsif ($agent =~ /Lynx/)
		{
			$agent =~ s/.*Lynx\/(.*?) .*/Lynx $1/;
		}
		elsif ($agent =~ /W3C_Validator/)
		{
			$agent =~ s/.*W3C_Validator\/(.*?) .*/W3C_Validator $1/;
		}
		elsif ($agent =~ /SVN/)
		{
			$agent =~ s/.*SVN\/(.*?) .*/SVN $1/;
		}
		elsif ($agent =~ /libwww-perl/)
		{
			$agent =~ s/.*libwww-perl\/(.*?)$/libwww-perl $1/;
		}
		elsif ($agent =~ /Wget/)
		{
			$agent =~ s/.*Wget\/(.*?)$/Wget $1/;
		}
		elsif ($agent =~ /Konqueror/)
		{
			$agent =~ s/.*Konqueror\/(.*?);.*/Konqueror $1/;
		}
		elsif ($agent =~ /MSIE/)
		{
			$agent =~ s/.*(MSIE .*?);.*/$1/;
		}

		next if $host =~ /(localhost|leighmardon\.com\.au|endbracket\.net|mikelward\.com)/;
		next if $address =~ /\.(css|inc|htc|js|bmp|gif|ico|png|jpg|jpeg)/i;
		next if $address =~ /\/mail/;
		next if $address =~ /!svn/;
		next if $agent =~ /(Ask Jeeves|Baiduspider|BecomeBot|BlogPulse|BlogSearch|bot|Browsershots|Charlotte|Crawler|Exabot|Feedfetcher-Google|findlinks|Googlebot|heritrix|HouxouCrawler|Kalooga|ICC-Crawler|larbin|Moreoverbot|msnbot|MSRBOT|NaverBot|NetSeer|Netcraft Web Server Survey|PHP version tracker|psbot|R6_FeedFetcher|relevantnoise\.com|Rome Client|SBIder|Shelob|Snapbot|Sogou web spider|Speedy Spider|Sphere Scout|Spider|SurveyBot|Technoratibot|TestSpider|T-H-U-N-D-E-R-S-T-O-N-E|TMCrawler|Twiceler|Twingly Recon|VoilaBot|W3C_Validator|WebAlta Crawler|Yahoo! Slurp|Yanga|Yeti|YoudaoBot)/;

		next if $status != 200;

		if ($host)
		{
			my @addressbits = split /\//, $address;
			my $shortaddress = '/' . $addressbits[1];
			if (@addressbits > 2) {
				$shortaddress .= '/' . $addressbits[-1];
			}

			my $referrerdomain = $referrer;
			$referrerdomain =~ s,^https?://,,;
			$referrerdomain =~ s,/.*,,;

			my $query = $referrer;
			$query =~ s,^.*?[?],,;
			#print "query=$query ";
			my @params = split /[?&]/, $query;
			my %param;
			foreach my $param (@params) {
				#print "$param ";
				#$param =~ /^(.*?)(?:=(.*))?/;
				if ($param =~ /=/) {
					$param =~ /^(.*?)=(.*)/;
					$param{$1} = $2 || '';;
				}
				else {
					$param{$1} = $param || '';
				}
				#$param{$1} = $2 || '';;
				#print "$1=$2 ";
			}
			my $searchterm;# = $query;
			if ($referrerdomain =~ /images.google/) {
				$searchterm = $param{'prev'};
				$searchterm =~ s,/images%3Fq%3D,,;
				$searchterm =~ s,%2B,+,g;
			}
			elsif ($referrerdomain =~ /google/) {
				$searchterm = $param{'q'};
			}
			elsif ($referrerdomain =~ /live.com/) {
				$searchterm = $param{'q'};
			}
			elsif ($referrerdomain =~ /images.*yahoo/) {
				$searchterm = $param{'p'};
			}
			$searchterm =~ s/\+/ /g;

			#print $date . "\t" . $host . "\t" . $address . "\t" . $agent . "\n";
			#printf "%-26s\t%-48s\t%-46s\t%-20s\n", $date, $host, $address, $agent;
			#printf "%-48s\t%-46s\t%-20s\n", $host, $shortaddress, $agent;
			#printf "%-30s\t%-12s\t%-30s\n", $shortaddress, $referrerdomain, $searchterm;
			if ($searchterm =~ /\S/) {
				printf "%-30s\t%-30s\n", $shortaddress, $searchterm;
			}
			#print $agent . "\n";
			#print $address . "\n";
			#print $shortaddress . "\n";
		}
		else
		{
			print "NO MATCH: $_\n";
		}
	}
}

#grep -E -v '^([^ ]*\.)?(leighmardon\.com\.au|endbracket\.net|mikelward\.com|googlebot\.com|live\.com|inktomisearch\.com|phx\.gbll)' /var/log/apache2/combined.log | grep -E -v '\.(css|js|ico|png|jpg|jpeg)\>' | grep -E -v '\<(Baiduspider|msnbot|MSRBOT|Rome Client)\>'
