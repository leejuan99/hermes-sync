<?php
/**
 * 00_bootstrap_cleanup.php — Novamira Sandbox Pollution Prevention
 * 
 * This file runs FIRST alphabetically due to the "00_" prefix.
 * It disables any test PHP files that output to stdout and would
 * pollute the JSON-RPC stream used by the Novamira MCP server.
 * 
 * Place in: wp-content/novamira-sandbox/00_bootstrap_cleanup.php
 */

// Disable the known polluting test file
$test_file = __DIR__ . '/test_write.php';
if (file_exists($test_file)) {
    rename($test_file, $test_file . '.disabled');
}

// Disable any other test_*.php files that might output to stdout
$test_files = glob(__DIR__ . '/test_*.php');
foreach ($test_files as $file) {
    if (basename($file) !== '00_bootstrap_cleanup.php') {
        rename($file, $file . '.disabled');
    }
}

// Optional: log what was disabled (to PHP error log, not stdout!)
$disabled = array_filter(glob(__DIR__ . '/*.php.disabled'), fn($f) => !str_ends_with($f, '00_bootstrap_cleanup.php'));
if ($disabled) {
    error_log('[Novamira Cleanup] Disabled sandbox files: ' . implode(', ', array_map('basename', $disabled)));
}