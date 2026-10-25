<?php
// T13: Filename supplied by the client; do not execute this fixture.
// Expected: VULNERABLE if sent unescaped into a shell command.
$filename = $_FILES['upload']['name'];
system('echo ' . $filename);
