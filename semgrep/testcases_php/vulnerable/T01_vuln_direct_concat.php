<?php
// T01 - Vulnerable: du lieu request noi truc tiep vao lenh (giong DVWA low).
// Nhan chuan: VULNERABLE
// ruleid: php-os-command-injection-taint
$out = shell_exec('ping -c 4 ' . $_GET['ip']);
echo "<pre>$out</pre>";
