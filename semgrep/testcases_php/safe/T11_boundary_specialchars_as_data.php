<?php
// T11 - Boundary: chuoi co ; | & $( ) nhung chi xu ly nhu du lieu (ghi file, in ra),
// khong di vao sink thuc thi lenh.
// Nhan chuan: SAFE
$note = $_POST['note'];   // vi du: "a; b | c && $(d)"
file_put_contents('/tmp/notes.txt', $note . PHP_EOL, FILE_APPEND);
echo htmlspecialchars($note);
// ok: php-os-command-injection-taint
system('wc -l /tmp/notes.txt');
