#!/usr/bin/perl
# vim: set tw=0:

#my $logfile = "/var/log/apache2/combined.log";
#my $logfile = "/home/mikelward/logs/mikelward.com/http/access.log.0";
#my $logfile = "/home/mikelward/logs/mikelward.com/http/access.log";

#open(LOGFILE, "<$logfile")
#    or die "Cannot open log file";

use strict;
use warnings;

my %country;
while (<>)
{
    chomp;
    #remotehost rfc931 authuser [date] "request" status bytes "referer" "user_agent"
    /([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" (\d+) ([^ ]*) "([^"]*)" "([^"]*)"/;

	my ($host, $ident, $user, $date, $request, $status, $bytes, $referer, $agent);
    $host = $1;
    $ident = $2;
    $user = $3;
    $date = $4;
    $request = $5;
    $status = $6;
    $bytes = $7;
    $referer = $8;
    $agent = $9;

	my $address;
    $address = $request;
    $address =~ s/^([A-Z]*) //;
    $address =~ s/ HTTP[^ ]*$//;
    $address =~ s/\?.*//;
    $address =~ s/^\/michael//;

	my $country;
	if (!defined($country{$host}))
	{
		$country = `geoip-lookup $host`;
		chomp $country;
		$country{$host} = $country;
	}
	else
	{
		$country = $country{$host};
	}

	my $platform;
	if ($agent =~ /^Mozilla\/\S*\s*\((.*?)\)/)
	{
		my @platformbits = split /\s*;\s*/, $1;
		# e.g. grab Linux i686 out of (X11; U; Linux i686; en-US)
		if (@platformbits >= 3)
		{
			$platform = $platformbits[2];
			if ($platform =~ /^Windows/) {
				if ($platform eq "Windows NT 6.0") { $platform = "Windows Vista"; }
				elsif ($platform eq "Windows NT 6.1") { $platform = "Windows 7"; }
				elsif ($platform eq "Windows NT 5.2") { $platform = "Windows 2003"; }
				elsif ($platform eq "Windows NT 5.1") { $platform = "Windows XP"; }
			}
			#elsif ($platform =~ /Intel Mac OS X (\d+)_(\d+)_?.*/) {
			#$platform = "Mac OS $1.$2";
			#}
			elsif ($platform =~ /^(Intel|PPC) Mac OS X/) {
				$platform = "Mac OS X";
			}
			elsif ($platform =~ /^Linux/) {
				$platform = "Linux";
			}
			elsif ($platform =~ /^Android/) {
				$platform = "Android";
			}
			elsif ($platform =~ /^CPU iPhone OS/) {
				$platform = "iPhone";
			}
		}
		else
		{
			#print STDERR scalar(@platformbits) . " bits: " . (join "; ", @platformbits) . "\n";
			$platform = "";
		}
	}
	else
	{
		$platform = "";
	}

    if ($agent =~ /Opera/)
    {
        $agent =~ s/.*Opera\/(.*?) .*$/Opera $1/;
    }
	#elsif ($agent =~ /Epiphany/)
	#{
	#$agent =~ s/Epiphany[\/ ](.*?)/Epiphany $1/;
	#}
    elsif ($agent =~ /Safari/)
    {
        $agent =~ s/.*Safari[\/ ]([^ ]*).*/Safari $1/;
    }
    elsif ($agent =~ /AppleWebKit/)
    {
        $agent =~ s/.*AppleWebKit\/(.*?) .*$/AppleWebKit $1/;
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
	elsif ($agent =~ /^BlackBerry/)
	{
		$agent =~ s/^BlackBerry(\d+).*/BlackBerry $1/;
	}
    elsif ($agent =~ /MSIE/)
    {
        $agent =~ s/.*(MSIE .*?);.*/$1/;
    }

    next if $host =~ /(localhost|leighmardon\.com\.au|endbracket\.net|mikelward\.com)/;
    next if $address =~ /\.(css|inc|htc|js|bmp|gif|ico|png|jpg|jpeg)/i;
    next if $address =~ /\/mail/;
    next if $address =~ /!svn/;
    next if $agent =~ /(Apache \(internal dummy connection\)|Ask Jeeves|Baiduspider|BecomeBot|BlogPulse|BlogSearch|bot|Browsershots|butterfly|Charlotte|[Cc]rawler|Exabot|facebookexternalhit|Feedfetcher-Google|findlinks|Googlebot|heritrix|hs-HTTP|HouxouCrawler|ia_archiver|ICC-Crawler|Java|Jakarta Commons-HttpClient|justsignal|Kalooga|larbin|Mediapartners-Google|Moreoverbot|msnbot|MSRBOT|NaverBot|NetSeer|Netcraft Web Server Survey|PHP version tracker|psbot|R6_FeedFetcher|relevantnoise\.com|Rome Client|SBIder|Scout|Shelob|Snapbot|Sogou web spider|Sosospider|Speedy Spider|Sphere Scout|Spider|SurveyBot|Technoratibot|TestSpider|T-H-U-N-D-E-R-S-T-O-N-E|TMCrawler|Twiceler|Twingly Recon|VoilaBot|W3C_Validator|WebAlta Crawler|WordPress|Yahoo! Slurp|Yanga|Yeti|YoudaoBot)/;

    next if $status != 200;

    if ($host)
    {
		if (length($address) == 0)
		{
			print STDERR "No address for $host\n";
		}
		my @addressbits = split /\//, $address;
		my $shortaddress = '/';
		if (@addressbits > 0)
		{
			$shortaddress .= $addressbits[1];
		}
		if (@addressbits > 2)
		{
			$shortaddress .= '/' . $addressbits[-1];
		}

		my $referrerdomain = $referer;
		$referrerdomain =~ s,^[^/]*//,,;
		$referrerdomain =~ s,/.*,,;

        #print $date . "\t" . $host . "\t" . $address . "\t" . $agent . "\n";
		#printf "%-26s\t%-48s\t%-46s\t%-20s\n", $date, $host, $address, $agent;
		#printf "%-26s\t%-18s\t%-2s\t%-18s\t%-40s\n", $date, $host, $country, $agent, $shortaddress;
		printf "%-26s\t%-18s\t%-2s\t%-18s\t%-18s\t%-40s\n", $date, $host, $country, $agent, $platform, $shortaddress;
		#print $agent . "\n";
		#print $address . "\n";
		#print $shortaddress . "\n";
    }
    else
    {
        print "NO MATCH: $_\n";
    }
}

#grep -E -v '^([^ ]*\.)?(leighmardon\.com\.au|endbracket\.net|mikelward\.com|googlebot\.com|live\.com|inktomisearch\.com|phx\.gbll)' /var/log/apache2/combined.log | grep -E -v '\.(css|js|ico|png|jpg|jpeg)\>' | grep -E -v '\<(Baiduspider|msnbot|MSRBOT|Rome Client)\>'
