<?php
// T05 - Vulnerable: du lieu qua nhieu buoc gan bien.
// Nhan chuan: VULNERABLE
$a = $_REQUEST['dir'];
$b = trim($a);
$c = $b;
$cmd = "ls -la " . $c;
// ruleid: php-os-command-injection-taint
$h = popen($cmd, 'r');
echo fread($h, 4096);
pclose($h);
