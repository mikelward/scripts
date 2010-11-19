#!/usr/bin/perl
# vim: set tw=0:

#my $logfile = "/var/log/apache2/combined.log";
#my $logfile = "/home/mikelward/logs/mikelward.com/http/access.log.0";
#my $logfile = "/home/mikelward/logs/mikelward.com/http/access.log";

#open(LOGFILE, "<$logfile")
#    or die "Cannot open log file";

my %country;
while (<>)
{
    chomp;
    #remotehost rfc931 authuser [date] "request" status bytes "referer" "user_agent"
    /([^ ]*) ([^ ]*) ([^ ]*) \[([^]]*)\] "([^"]*)" (\d+) ([^ ]*) "([^"]*)" "([^"]*)"/;

    $host = $1;
    $ident = $2;
    $user = $3;
    $date = $4;
    $request = $5;
    $status = $6;
    $bytes = $7;
    $referer = $8;
    $agent = $9;

    $address = $request;
    $address =~ s/^([A-Z]*) //;
    $address =~ s/ HTTP[^ ]*$//;
    $address =~ s/\?.*//;
    $address =~ s/^\/michael//;

	if (!defined($country{$host})) {
		$country = `geoip-lookup $host`;
		chomp $country;
		$country{$host} = $country;
	}

    if (/Opera/)
    {
        $agent =~ s/.*Opera\/(.*?) .*$/Opera $1/;
    }
    elsif ($agent =~ /Safari/)
    {
        $agent =~ s/.*Safari\/(.*?)$/Safari $1/;
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
    elsif ($agent =~ /MSIE/)
    {
        $agent =~ s/.*(MSIE .*?);.*/$1/;
    }

    next if $host =~ /(localhost|leighmardon\.com\.au|endbracket\.net|mikelward\.com)/;
    next if $address =~ /\.(css|inc|htc|js|bmp|gif|ico|png|jpg|jpeg)/i;
    next if $address =~ /\/mail/;
    next if $address =~ /!svn/;
    next if $agent =~ /(Apache \(internal dummy connection\)|Ask Jeeves|Baiduspider|BecomeBot|BlogPulse|BlogSearch|bot|Browsershots|Charlotte|[Cc]rawler|Exabot|Feedfetcher-Google|findlinks|Googlebot|heritrix|HouxouCrawler|ia_archiver|Kalooga|ICC-Crawler|larbin|Moreoverbot|msnbot|MSRBOT|NaverBot|NetSeer|Netcraft Web Server Survey|PHP version tracker|psbot|R6_FeedFetcher|relevantnoise\.com|Rome Client|SBIder|Scout|Shelob|Snapbot|Sogou web spider|Speedy Spider|Sphere Scout|Spider|SurveyBot|Technoratibot|TestSpider|T-H-U-N-D-E-R-S-T-O-N-E|TMCrawler|Twiceler|Twingly Recon|VoilaBot|W3C_Validator|WebAlta Crawler|Yahoo! Slurp|Yanga|Yeti|YoudaoBot)/;

    next if $status != 200;

    if ($host)
    {
		my @addressbits = split /\//, $address;
		my $shortaddress = '/' . $addressbits[1];
		if (@addressbits > 2) {
			$shortaddress .= '/' . $addressbits[-1];
		}

		my $referrerdomain = $referrer,
		$referrerdomain =~ s,^[^/]*//,,;
		$referrerdomain =~ s,/.*,,;

        #print $date . "\t" . $host . "\t" . $address . "\t" . $agent . "\n";
		#printf "%-26s\t%-48s\t%-46s\t%-20s\n", $date, $host, $address, $agent;
		printf "%-26s\t%-18s\t%-2s\t%-18s\t%-40s\n", $date, $host, $country, $agent, $shortaddress;
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
