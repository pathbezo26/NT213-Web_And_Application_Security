<?php
// T12 - Boundary: co sink va co input, nhung input da qua escapeshellarg().
// Kiem tra rule co nhan dien sanitizer, tranh bao nham.
// Nhan chuan: SAFE
$ip = $_GET['ip'];
// ok: php-os-command-injection-taint
$out = shell_exec('ping -c 4 ' . escapeshellarg($ip));
echo "<pre>$out</pre>";
