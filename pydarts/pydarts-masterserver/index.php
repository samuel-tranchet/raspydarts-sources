<?php
// Config
//$db='/var/www/html/pydarts-masterserver/master-server.db';//absolute path
$db='master-server.db';//relative to php script folder
$wiki='https://obilhaut.freeboxos.fr/pydarts-wiki';
$server='obilhaut.freeboxos.fr';
$serverport=5005;
$masterport=5006;
$delim="|";

// Include
include_once('servertest.php');

$server_version=getServerVersion($server,$serverport,True,$delim,True);

if ($server_version<0 or ! $server_version) {
        $txt_server_running = 'Error binding official game server ('.$server.' on port '.$serverport.' : error '.$server_version.'). Server is probably down. Please contact maintainers.';
        $server_status='nok';
}
else {
        $txt_server_running = "Official Game server ".$server." is up (version ".$server_version.") !";
        $server_status='ok';
}

$master_version=getServerVersion($server,$masterport,False,"",False);

if ($master_version<0 or ! $master_version) {
        $txt_master_running = 'Error binding Master version ('.$server.' on port '.$masterport.' : error '.$master_version.'). Master Server is probably down. Please contact maintainers.';
        $master_status='nok';
}
else {
        $txt_master_running = "Official Master server ".$server." is up (version ".$master_version.") !";
        $master_status='ok';
}

// Check if a running server on this host
//$running = exec('ps -u admindebian | grep "python MasterServer.py"',$output);
/*
$master_running = exec('ps a | grep -v "ps a" | grep -v "grep" | grep -c MasterServer.py',$output);

if ($master_running==0){$txt_master_running="Master Server seems down on this host.";}
if ($master_running==1){$txt_master_running="Master Server is up right now.";}
if ($master_running>1){$txt_master_running="Warning : multiple Master Server instances detected";}

*/

// Test SQlite3 support
if(!class_exists('SQLite3'))
	die("SQLite 3 NOT supported.");

// Connect
try {
	// Nouvel objet de base SQLite 
	$db_handle = new PDO('sqlite:'.$db);
	// Quelques options
	$db_handle->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (Exception $e) {
	die('Connexion error : '.$e->getMessage());
}

// Create database
try {
	// Table creation if it doesnt not exists
	$create = $db_handle->exec("CREATE TABLE IF NOT EXISTS mails (id INTEGER PRIMARY KEY AUTOINCREMENT, mail TEXT UNIQUE);");
} finally {
	echo "";
}

// Save data
if ($_POST['register-submit'] && $_POST['register-mail']!="") {
	try {
		$sql = $db_handle->prepare("SELECT * FROM mails WHERE mail='".$_POST['register-mail']."'");
		$sql->execute();
		$nb = count($sql->fetchAll(PDO::FETCH_ASSOC));
		if ($nb==0) {
			$registration_submited="Email registered. You'll receive notices for network games on this server !";
			$insert = $db_handle->exec("INSERT OR IGNORE INTO mails(mail) VALUES('".$_POST['register-mail']."')");
			}
		else {
			$registration_submited="Email deleted from database... You'll not receive any notice anymore.";
			$delete = $db_handle->exec("DELETE FROM mails WHERE mail='".$_POST['register-mail']."'");
			}
	} catch (Exception $e) {
		die("Error inserting/removing email : ".$e."<br />");
	}
}

// Display list of registred users
if ($_GET['list']) {
	try {
		$sql = $db_handle->prepare("SELECT * FROM mails LIMIT 5000");
		$sql->execute();
		$res = $sql->fetchAll(PDO::FETCH_ASSOC);
		$nb = count($res);
		$list.=$nb.' registered e-mails :<br />
		<table id="registered-table">';
		foreach ($res as $line) {
			$list.="<tr><td>".$line['mail']."</td></tr>";
		}
		$list.='</table>';

	} catch (Exception $e) {
                die("Error getting email list : ".$e."<br />");
        }

}

// Display list of opened games
if (True) {
	try {
		$sql = $db_handle->prepare("SELECT * FROM games WHERE status='1' LIMIT 100");
		$sql->execute();
		$res = $sql->fetchAll(PDO::FETCH_ASSOC);
		$nb = count($res);
		if ($nb>0) {
			$gamelist.='<span class="gamelist-title">'.$nb.' game(s) opened :</span><br />
				<table id="gamelist-table">
				<th>Game name</th><th>Game type</th><th>Number of players</th>';
			foreach ($res as $line) {
				$gamelist.="<tr><td>".$line['gamename']."</td><td>".$line['gametype']."</td><td>".$line['players']."</td></tr>";
			}
			$gamelist.='</table>';
		}	else {
			$gamelist='No game waiting on this Server right now.';
		}
		} catch (Exception $e) {
						 die("Error getting game list : ".$e."<br />");
			  }
}

// Display list of archived games
if (True) {
	try {
		$sql = $db_handle->prepare("SELECT * FROM games WHERE status='0' ORDER BY creation_timestamp DESC LIMIT 1000");
		$sql->execute();
		$res = $sql->fetchAll(PDO::FETCH_ASSOC);
		$nb = count($res);
		if ($nb>0) {
			$archived_gamelist.='<span class="archived-gamelist-title">'.$nb.' game(s) archived :</span><br />
				<table id="archived-gamelist-table">
				<th>Date</th><th>Game name</th><th>Game type</th><th>Number of players</th>';
			foreach ($res as $line) {
				$archived_gamelist.="<tr><td>".$line['creation_timestamp']."</td><td>".$line['gamename']."</td><td>".$line['gametype']."</td><td>".$line['players']."</td></tr>";
			}
			$archived_gamelist.='</table>';
		}
		else {
			$archived_gamelist='No archived games on this server for now...';
			}
	}
	catch (Exception $e) {
		die("Error getting archived game list : ".$e."<br />");
		}
}

// Display form
echo '<!DOCTYPE html>
	<html>
	<header>
		<link rel="stylesheet" type="text/css" media="all" href="css/style.css" />
		<title>pyDarts Web Administration Interface</title>
	</header>
	<body>
	<div class="logo-container"><img src="logo.png" class="logo" />pyDarts Web Administration Interface</div>';

//echo '<div class="server-running running-'.$master_running.'">'.$txt_master_running.'</div>';

	echo '<div class="server-info-container">';
		echo '<div class="section-title">pyDarts servers status</div>';
		echo '<div class="server-running running-'.$master_status.'">'.$txt_master_running.'</div>';
		echo '<div class="server-running running-'.$server_status.'">'.$txt_server_running.'</div>';
		echo '<div class="recommandations">On your side, please ensure to run the same version (eventually <a href=\"'.$wiki.'\" target=\"new\">read the wiki.</a>)</div>';
	echo '</div>';


	echo '
	<div class="form-container">
	<div class="section-title">Register to be notified when a network game is created</div>
		<form id="register" method="POST" class="register-form">
			<input type="text" id="register-mail" name="register-mail"  />
			<input type="submit" id="register-submit" name="register-submit" value="Register/Unregister"/>
		</form>
	</div>
	';


if ($registration_submited) echo '<div class="registration-result">'.$registration_submited.'</div>';
if ($list) echo '<div class="registered-list">'.$list.'</div>';
if ($gamelist) echo '<div class="gamelist">'.$gamelist.'</div>';
if ($archived_gamelist) echo '<div class="archived-gamelist">'.$archived_gamelist.'</div>';

echo '	</body>
	</html>';
?>
