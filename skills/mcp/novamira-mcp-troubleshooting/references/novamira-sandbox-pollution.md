# Novamira Sandbox Pollution — Critical Pitfall

## Problem

The Novamira WordPress plugin auto-loads **every PHP file in the sandbox directory (`wp-content/novamira-sandbox/`)** alphabetically on every WordPress request. Any PHP file that outputs to stdout (even a simple `echo`) will **pollute the JSON-RPC stream** used by the MCP server.

## Symptoms

- All MCP tool calls fail with: `Invalid Request: jsonrpc version must be '2.0'`
- Error: `Unexpected token 'e', "test write "... is not valid JSON`
- Error: `MCP error -32603: Cannot process tools/call: WordPress connection failed during initialization`
- The WordPress API returns the test file's output mixed with the JSON-RPC response
- **No MCP ability works** — not even `delete-file` or `disable-file`

## Root Cause

During testing, a file `test_write.php` was created:
```php
<?php echo 'test write success ' . date('Y-m-d H:i:s'); ?>
```

This file auto-loads on **every** JSON-RPC request, injecting output before the actual JSON-RPC response.

## Immediate Fix

Use `novamira/execute-php` (runs after WordPress init, may work even when JSON-RPC is polluted):

```json
{
  "ability_name": "novamira/execute-php",
  "parameters": {
    "code": "@unlink('/www/wwwroot/yoursite.com/wp-content/novamira-sandbox/test_write.php'); echo json_encode(['deleted' => true]);"
  }
}
```

## Robust Fix: Bootstrap Cleanup File

Create `00_bootstrap_cleanup.php` (runs first due to `00_` prefix):

```php
<?php
// 00_bootstrap_cleanup.php — runs first alphabetically
$test_file = __DIR__ . '/test_write.php';
if (file_exists($test_file)) {
    rename($test_file, $test_file . '.disabled');
}
```

Deploy via:
```json
{
  "ability_name": "novamira/write-file",
  "parameters": {
    "path": "wp-content/novamira-sandbox/00_bootstrap_cleanup.php",
    "content": "<?php\n// 00_bootstrap_cleanup.php — runs first alphabetically\n$test_file = __DIR__ . '/test_write.php';\nif (file_exists($test_file)) {\n    rename($test_file, $test_file . '.disabled');\n}\n"
  }
}
```

## Prevention Rules

1. **Never create PHP files in sandbox that output to stdout** — they auto-load and pollute JSON-RPC
2. **Prefix test files with `test_` and disable immediately** using `disable-file` or rename to `.disabled`
2. **Use `00_` prefix for bootstrap/cleanup files** that must run first
3. **Test MCP after any sandbox write**: `hermes mcp test <server>`

## Commands That Fail When Polluted

| Command | Fails Because |
|---------|---------------|
| `hermes mcp test <server>` | JSON-RPC handshake corrupted |
| `novamira/delete-file` | JSON-RPC request corrupted |
| `novamira/disable-file` | JSON-RPC request corrupted |
| `novamira/execute-php` | **May work** — runs after WP init |