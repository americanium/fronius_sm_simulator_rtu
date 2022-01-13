#!/usr/bin/perl

# Einbinden der LoxBerry-Module
use CGI;
use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::JSON;
use LoxBerry::Log;
  
# Die Version des Plugins wird direkt aus der Plugin-Datenbank gelesen.
my $version = LoxBerry::System::pluginversion();
 
# Mit dieser Konstruktion lesen wir uns alle POST-Parameter in den Namespace R.
my $cgi = CGI->new;
$cgi->import_names('R');
# Ab jetzt kann beispielsweise ein POST-Parameter 'form' ausgelesen werden mit $R::form.
 
 
# Wir Übergeben die Titelzeile (mit Versionsnummer), einen Link ins Wiki und das Hilfe-Template.
# Um die Sprache der Hilfe brauchen wir uns im Code nicht weiter zu kümmern.
LoxBerry::Web::lbheader("Sample Plugin for Perl V$version", "http://www.loxwiki.eu/x/2wN7AQ", "help.html");
  
# Wir holen uns die Plugin-Config in den Hash %pcfg. Damit kannst du die Parameter mit $pcfg{'Section.Label'} direkt auslesen.
#my %pcfg;
#tie %pcfg, "Config::Simple", "$lbpconfigdir/pluginconfig.cfg";
my $pcfg = new Config::Simple("$lbpconfigdir/config.cfg");


# Wir initialisieren unser Template. Der Pfad zum Templateverzeichnis steht in der globalen Variable $lbptemplatedir.

my $template = HTML::Template->new(
    filename => "$lbptemplatedir/index.html",
    global_vars => 1,
    loop_context_vars => 1,
    die_on_bad_params => 0,
	associate => $cgi,
);
  
# Jetzt lassen wir uns die Sprachphrasen lesen. Ohne Pfadangabe wird im Ordner lang nach language_de.ini, language_en.ini usw. gesucht.
# Wir kümmern uns im Code nicht weiter darum, welche Sprache nun zu lesen wäre.
# Mit der Routine wird die Sprache direkt ins Template übernommen. Sollten wir trotzdem im Code eine brauchen, bekommen
# wir auch noch einen Hash zurück.
my %L = LoxBerry::Web::readlanguage($template, "language.ini");
  
my $lastdata;
my $status =1;
my %pids;

# ----------------------------------
#our %navbar;
#$navbar{1}{Name} = "First Menu";
#$navbar{1}{URL} = 'index.cgi';

#$navbar{2}{Name} = "Second Menu";
#$navbar{2}{URL} = 'second.cgi';
#$navbar{2}{active} = 1;

#$navbar{3}{Name} = "External Website";
#$navbar{3}{URL} = 'http://www.loxberry.de';
#$navbar{3}{target} = '_blank';

#LoxBerry::Web::lbheader($plugintitle, $helplink, $helptemplate);

# -----------------------------

if( $q->{ajax} ) {

# Get pids
if( $q->{ajax} eq "getpids" ) {
pids();
$response{pids} = \%pids;
print JSON->new->canonical(1)->encode(\%response);
}

sub pids
{
	$pids{'owserver'} = trim(`pgrep -f owserver`) ;
	$pids{'owhttpd'} = trim(`pgrep -f owhttpd`) ;
	$pids{'owfs2mqtt'} = trim(`pgrep -d , -f owfs2mqtt`) ;
	return();
}

} else {

# ---------------------------------------------------
# Save settings to config file
# ---------------------------------------------------
if ($R::btnSave)
{
	$pcfg->param('CONFIGURATION.TOPIC_CONSUMPTION', $R::txtMQTTTopicConsumption);
	$pcfg->param('CONFIGURATION.TOPIC_TOTAL_IMPORT', $R::txtMQTTTopicExport);
	$pcfg->param('CONFIGURATION.TOPIC_TOTAL_EXPORT', $R::txtMQTTTopicImport);
   	$pcfg->param('CONFIGURATION.CORRFACTOR', $R::txtCorrectionFactor);
    	$pcfg->param('CONFIGURATION.SERIAL_PORT', $R::txtSerialPort);

	$pcfg->save();
}


if ($R::btnReStart)
{

system("pkill -f frsmsimulator");
system("python $lbpbindir/frsmsimulator.py -h $lbhomedir &");
#&state;


}


if ($R::btnStop)
{

system("pkill -f frsmsimulator"); 
#&state;

}

# ---------------------------------------------------
# Control for "frmStart" Form
# ---------------------------------------------------
my $frmStart = $cgi->start_form(
      -name    => 'FrosimPlugIn',
      -method => 'POST',
  );
$template->param( frmStart => $frmStart );


# ---------------------------------------------------
# Control for "frmEnd" Form
# ---------------------------------------------------
my $frmEnd = $cgi->end_form();
$template->param( frmEnd => $frmEnd );




# ---------------------------------------------------
# Control for "txtMQTTTopicConsumption" Textfield
# ---------------------------------------------------
my $txtMQTTTopicConsumption = $cgi->textfield(
      -name    => 'txtMQTTTopicConsumption',
      -default => $pcfg->param('CONFIGURATION.TOPIC_CONSUMPTION'),
  );
$template->param( txtMQTTTopicConsumption => $txtMQTTTopicConsumption );

# ---------------------------------------------------
# Control for "txtMQTTTopicImport" Textfield
# ---------------------------------------------------
my $txtMQTTTopicImport = $cgi->textfield(
      -name    => 'txtMQTTTopicImport',
      -default => $pcfg->param('CONFIGURATION.TOPIC_TOTAL_IMPORT'),
  );
$template->param( txtMQTTTopicImport => $txtMQTTTopicImport );

# ---------------------------------------------------
# Control for "txtMQTTTopicExport" Textfield
# ---------------------------------------------------
my $txtMQTTTopicExport = $cgi->textfield(
      -name    => 'txtMQTTTopicExport',
      -default => $pcfg->param('CONFIGURATION.TOPIC_TOTAL_EXPORT'),
  );
$template->param( txtMQTTTopicExport => $txtMQTTTopicExport );

# ---------------------------------------------------
# Control for "txtCorrectionFactor" Textfield
# ---------------------------------------------------
my $txtCorrectionFactor = $cgi->textfield(
      -name    => 'txtCorrectionFactor',
      -default => $pcfg->param('CONFIGURATION.CORRFACTOR'),
  );
$template->param( txtCorrectionFactor => $txtCorrectionFactor );

# ---------------------------------------------------
# Control for "txtSerialPort" Textfield
# ---------------------------------------------------
my $txtSerialPort = $cgi->textfield(
      -name    => 'txtSerialPort',
      -default => $pcfg->param('CONFIGURATION.SERIAL_PORT'),
  );
$template->param( txtSerialPort => $txtSerialPort );

# ---------------------------------------------------
# Control for "btnSave" Button
# ---------------------------------------------------
my $btnSave = $cgi->submit(
      -name    => 'btnSave',
      -value => $L{'CONFIGURATION.btnSave'},
  );
$template->param( btnSave => $btnSave );

# ---------------------------------------------------
# Control for "btnReStart" Button
# ---------------------------------------------------
my $btnReStart = $cgi->submit(
      -name    => 'btnReStart',
      -value => $L{'CONFIGURATION.btnReStart'},
  );
$template->param( btnReStart => $btnReStart);


# ---------------------------------------------------
# Control for "btnStop" Button
# ---------------------------------------------------
my $btnStop = $cgi->submit(
      -name    => 'btnStop',
      -value => $L{'CONFIGURATION.btnStop'},
  );
$template->param( btnStop => $btnStop);

# Den so erzeugten HTML-Code schreiben wir ins Template.

$template->param( ACTIVATED => $activated);

# ---------------------------------------------------
# Evaluating status and PID of script runnning
# ---------------------------------------------------

#sub state
#{

my ($exitcode, $pid) = execute("pgrep -f frsmsimulator.py");

if ($pid == 0)
{
   $status = "Service stopped";

}elsif ($pid != 0)
{
   
   $status = "Service running";
}

$template->param( PID => $pid);
$template->param( STATUS => $status);
#}

# ---------------------------------------------------
# Localized Labels from language.ini
# ---------------------------------------------------

$template->param( lblMQTTTopicConsumption => $L{'CONFIGURATION.lblMQTTTopicConsumption'} );
$template->param( lblMQTTTopicImport => $L{'CONFIGURATION.lblMQTTTopicImport'}  );
$template->param( lblMQTTTopicExport => $L{'CONFIGURATION.lblMQTTTopicExport'}  );
$template->param( lblCorrectionFactor => $L{'CONFIGURATION.lblCorrectionFactor'}  );
$template->param( lblSerialPort => $L{'CONFIGURATION.lblSerialPort'}  );


# Nun wird das Template ausgegeben.
print $template->output();
  

# Schlussendlich lassen wir noch den Footer ausgeben.
LoxBerry::Web::lbfooter();
}
