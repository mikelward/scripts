#!/usr/bin/perl
# vim: set tw=0:


open(LOGFILE, "</var/log/apache2/combined.log")
    or die "Cannot open log file";

while (<LOGFILE>)
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

    if (/Opera/)
    {
        $agent =~ s/.*Opera\/(.*?)$/Opera $1/;
    }
    elsif ($agent =~ /Safari/)
    {
        $agent =~ s/.*Safari\/(.*?)$/Safari $1/;
    }
    elsif ($agent =~ /(Firefox|BonEcho)/)
    {
        $agent =~ s/.*(?:Firefox|BonEcho)\/(.*?)( .*|$)/Firefox $1/;
    }
    elsif ($agent =~ /SeaMonkey/)
    {
        $agent =~ s/.*SeaMonkey\/(.*?)$/SeaMonkey $1/;
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
    next if $agent =~ /(Ask Jeeves|Baiduspider|BecomeBot|BlogPulse|BlogSearch|bot|Browsershots|Exabot|Feedfetcher-Google|findlinks|Googlebot|heritrix|HouxouCrawler|ICC-Crawler|larbin|Moreoverbot|msnbot|MSRBOT|Netcraft Web Server Survey|PHP version tracker|psbot|relevantnoise\.com|Rome Client|SBIder|Snapbot|Sogou web spider|Speedy Spider|SurveyBot|Technoratibot|T-H-U-N-D-E-R-S-T-O-N-E|TMCrawler|Twiceler|Twingly Recon|VoilaBot|W3C_Validator|Yahoo! Slurp|Yeti)/;

    next if $status != 200;

    if ($host)
    {
        #print $date . "\t" . $host . "\t" . $address . "\t" . $agent . "\n";
        printf "%-26s\t%-48s\t%-46s\t%-20s\n", $date, $host, $address, $agent;
        #print $agent . "\n";
        #print $address . "\n";
    }
    else
    {
        print "NO MATCH: $_\n";
    }
}

#grep -E -v '^([^ ]*\.)?(leighmardon\.com\.au|endbracket\.net|mikelward\.com|googlebot\.com|live\.com|inktomisearch\.com|phx\.gbll)' /var/log/apache2/combined.log | grep -E -v '\.(css|js|ico|png|jpg|jpeg)\>' | grep -E -v '\<(Baiduspider|msnbot|MSRBOT|Rome Client)\>'
