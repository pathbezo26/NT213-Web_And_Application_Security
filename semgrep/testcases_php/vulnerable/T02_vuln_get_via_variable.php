<?php
// T02 - Vulnerable: GET di qua bien trung gian roi toi sink.
// Nhan chuan: VULNERABLE
$target = $_GET['host'];
// ruleid: php-os-command-injection-taint
system("nslookup " . $target);
