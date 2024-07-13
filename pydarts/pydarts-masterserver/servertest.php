<?php
function getServerVersion($host,$port, $givegamename=True, $delim="|", $ack=True, $timeout = 5) {
	$ret="Problem";
	// Timeout 
	set_time_limit($timeout);
	//error_reporting(E_ALL);
	// Turn on implicit output flushing so we see what we're getting as it comes in.
	ob_implicit_flush();
        if ($givegamename) { $txt_gamename='"GAMENAME":"NONE",';}
        else $txt_gamename="";
	$message='{'.$txt_gamename.' "REQUEST": "GETVERSION"}'.$delim;
	$ackmsg = '{"REQUEST": "ACK"}'.$delim;
	//echo "Creating socket...";
        $socket = socket_create(AF_INET, SOCK_STREAM, 0);
        if (! $socket) return -1;
	//echo "Socket created";
        $result = socket_connect($socket, $host, $port);
        if (! $result) return -2;
	//echo "Connected to server";
        $result=socket_write($socket, $message, strlen($message));
        if (! $result) return -3;
        if ($ack) {
                //echo "Writed message";
                $result = socket_read ($socket, 1024);
                //print("Received :".$result);
                if (! $result) return -4;
                if ($result != $ackmsg) return -5;
        }
	//echo "Reading...";
	if ($result == $ackmsg or !$ack) {
                try {
                        $result = socket_read ($socket, 1024);
                        if (! $result) return -6;
                        //echo "Reading...";
                        //echo "Reply From Server  :".$result;
                        $info = json_decode(rtrim($result,"|"), True);
                        $ret=$info['VERSION'];
                        }
                catch (Exception $e) {
                        return -7;
                        }
		}
        $result=socket_close($socket);
        #if (! $result) return -8;
	return $ret;
	}
?>
