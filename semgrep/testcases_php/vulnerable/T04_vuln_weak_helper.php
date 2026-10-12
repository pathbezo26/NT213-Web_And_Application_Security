<?php
// T04 - Vulnerable: helper tu viet chi xoa ';' -> van bypass bang | && $( ) xuong dong.
// Nhan chuan: VULNERABLE
function clean_input($s) {
    return str_replace(';', '', $s);
}
$ip = clean_input($_GET['ip']);
// ruleid: php-os-command-injection-taint
exec("ping -c 4 " . $ip, $lines);
print_r($lines);
