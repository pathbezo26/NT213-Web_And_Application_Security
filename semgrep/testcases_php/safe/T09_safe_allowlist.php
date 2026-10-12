<?php
// T09 - Safe: allowlist theo nghiep vu, lenh chi lay tu gia tri co dinh.
// Nhan chuan: SAFE
switch ($_GET['action'] ?? '') {
    case 'disk':   $cmd = 'df -h';   break;
    case 'uptime': $cmd = 'uptime';  break;
    default:       $cmd = 'whoami';
}
// ok: php-os-command-injection-taint
echo shell_exec($cmd);
