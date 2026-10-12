<?php
// T10 - Safe: gia tri co dinh, khong chiu anh huong tu nguoi dung.
// Nhan chuan: SAFE
// ok: php-os-command-injection-taint
system('uptime');
// ok: php-os-command-injection-taint
$out = shell_exec('date +%Y-%m-%d');
echo $out;
