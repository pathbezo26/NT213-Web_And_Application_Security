<?php
// T08 - Safe: proc_open voi mang doi so (PHP >= 7.4) -> khong qua /bin/sh,
// ky tu ; | & trong $host chi la du lieu cua doi so.
// Nhan chuan: SAFE
$host = $_GET['host'];
$spec = [1 => ['pipe', 'w']];
// ok: php-os-command-injection-taint
$p = proc_open(['ping', '-c', '4', $host], $spec, $pipes);
echo stream_get_contents($pipes[1]);
proc_close($p);
