<?php
// T07 - Safe: dung API PHP thay vi goi shell (khong co sink).
// Nhan chuan: SAFE
$dir = basename($_GET['dir'] ?? 'public');
// ok: php-os-command-injection-taint
$files = scandir('/var/www/data/' . $dir);
foreach ($files as $f) { echo htmlspecialchars($f) . "<br>"; }
