<?php
// T03 - Vulnerable: du lieu POST ghep vao lenh.
// Nhan chuan: VULNERABLE
$file = $_POST['filename'];
// ruleid: php-os-command-injection-taint
passthru("cat /var/www/uploads/" . $file);
