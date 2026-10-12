<?php
// T06 - Vulnerable: lenh duoc dung bang sprintf / noi chuoi truoc khi toi sink.
// Nhan chuan: VULNERABLE
$user = $_COOKIE['user'];
$cmd = sprintf("grep %s /var/log/app.log", $user);
// ruleid: php-os-command-injection-taint
system($cmd);
