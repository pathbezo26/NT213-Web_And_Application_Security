<?php
// T14: Backtick operator executes a shell command; do not execute this fixture.
// Expected: VULNERABLE if user-supplied input enters the command.
$user = $_GET['user'];
$out = `echo $user`;
echo $out;
