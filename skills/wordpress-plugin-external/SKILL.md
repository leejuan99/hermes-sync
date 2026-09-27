---
name: wordpress-plugin-external
description: "Develop WordPress plugins with external APIs, n8n, and AI."
---

You are building a WordPress plugin that needs to interact with external APIs, handle scheduled tasks via n8n webhooks, and provide AI-powered content generation. Follow this procedure to ensure a maintainable, secure, and WordPress‑standard‑compliant plugin.

## Procedure

1. **Set up the plugin folder and main file**
   - Create a folder under `wp-content/plugins/` with a unique slug (e.g., `my-plugin`).
   - Create the main PHP file with the standard plugin header.
   - Define constants for version, plugin dir, plugin url, and plugin file.

2. **Set up an autoloader**
   - Use `spl_autoload_register` to load classes from an `includes/` directory.
   - Follow PSR‑4 style: map namespace `SSA\` to `includes/`.
   - Example:
     ```php
     spl_autoload_register(function ($class) {
         $prefix = 'SSA\\';
         $base_dir = SSA_PLUGIN_DIR . 'includes/';
         $len = strlen($prefix);
         if (strncmp($prefix, $class, $len) !== 0) {
             return;
         }
         $relative_class = substr($class, $len);
         $file = $base_dir . str_replace('\\', '/', $relative_class) . '.php';
         if (file_exists($file)) {
             require_once $file;
         }
     });
     ```

3. **Include core components**
   - Require admin menu class, admin UI classes (accounts, content studio, repurpose hub, calendar, analytics).
   - Require manager classes: entity, composio client, content manager, AI generator, repurpose manager, scheduler.
   - Require DB schema and REST API endpoints.

4. **Register activation and deactivation hooks**
   - On activation: create custom tables via a schema class, flush rewrite rules, set default options.
   - On deactivation: flush rewrite rules.

5. **Register capabilities**
   - Define custom capabilities (e.g., `ssa_manage_own_accounts`, `ssa_create_content`, `ssa_schedule_posts`, `ssa_view_analytics`, `ssa_manage_templates`, `ssa_manage_settings`, `ssa_manage_all_users`).
   - Assign them to roles (author, editor, administrator) via `get_role()->add_cap()`.

6. **Initialize managers**
   - Instantiate singleton managers (entity, composio client, content manager, AI generator, repurpose manager, scheduler) in `init_managers()`.

7. **Admin menu**
   - Add a top‑level menu page and submenu pages for dashboard, social accounts, content studio, AI generator, repurpose hub, templates, schedule calendar, analytics, settings, logs.
   - Use `add_menu_page` and `add_submenu_page` with appropriate capability checks.

8. **Admin UI and views**
   - Separate UI logic (admin classes) from view templates (admin/views/).
   - Use `include` to load view PHP files.
   - Enqueue admin CSS and JS only on plugin admin pages via `admin_enqueue_scripts` hook.

9. **AJAX handlers**
   - Register AJAX actions with `wp_ajax_{action}` and `wp_ajax_nopriv_{action}` if needed.
   - Always check nonce (`check_ajax_referer` or `wp_verify_nonce`).
   - Check user capability (`current_user_can`).
   - Return JSON responses with `wp_send_json_success` or `wp_send_json_error`.

10. **Settings page**
    - Store options using `add_option`, `get_option`, `update_option` with a plugin prefix (e.g., `ssa_`).
    - Provide fields for Composio API key, AI provider keys, n8n webhook URL/secret, encryption salt.
    - Include a button to regenerate webhook secret.

11. **Social Accounts UI**
    - Use Composio API to generate OAuth connection URLs: `POST /connected_accounts/link` with `entity_id` (derived from WP user ID) and `toolkit`.
    - Save the returned account info (encrypted) to a custom table (`wp_ssa_accounts`).
    - Provide a disconnect button that deletes the account.

12. **Content Studio**
    - Implement CRUD for content (draft, scheduled, published) in a custom table (`wp_ssa_content`).
    - Provide AI generation: call AI provider (OpenRouter, OpenAI, Anthropic, Google) with prompt templates.
    - Provide template management: store AI templates in `wp_ssa_ai_templates` with variables and target platforms.
    - Provide repurpose hub: extract ideas from sources (YouTube, RSS, Twitter thread, URL) using AI, then generate platform‑specific variants.

13. **Scheduler / n8n Integration**
    - Expose a REST endpoint (e.g., `/wp-json/ssa/v1/due-posts`) that n8n can call to fetch scheduled content.
    - n8n workflow: fetch due posts, loop over them, call Composio execute tool for each platform, then POST results back to WordPress callback endpoint.
    - WordPress callback endpoint (`/wp-json/ssa/v1/content-callback`) updates post status and logs metrics.

14. **Encryption**
    - Store secrets (API tokens, API keys) encrypted with AES‑256‑GCM.
    - Keep the encryption key in `wp-config.php` as a constant (e.g., `SSA_ENCRYPTION_KEY`).
    - Provide helper functions `ssa_encrypt()` and `ssa_decrypt()`.

15. **Localization**
    - Load text domain with `load_plugin_textdomain`.
    - Wrap all user‑visible strings in `__()` or `_x()`.

16. **Enqueue assets conditionally**
    - In `admin_enqueue_scripts`, check `$hook` contains your plugin’s page prefix (e.g., `ssa-`) to avoid loading assets on every admin page.

17. **Logging and debugging**
    - Enable `WP_DEBUG` and `WP_DEBUG_LOG` in `wp-config.php` during development.
    - Write debug logs to `wp-content/debug.log` or a plugin‑specific log.
    - Provide a logs admin page to view and clear logs.

## Pitfalls

- **PHP syntax errors** – always run `php -l` on each .php file before activation; a missing brace or extra `}` will cause a fatal error that blocks activation.
- **Missing autoloader registration** – leads to "class not found" errors; ensure the autoloader is registered before any class is used.
- **Failing to flush rewrite rules** – causes 404s for custom endpoints; flush on activation and deactivation.
- **Incorrect capability checks** – users may see "Unauthorized" or gain unintended access; always verify `current_user_can` for the specific capability.
- **Nonce missing or invalid** – AJAX requests fail with "403 Forbidden"; use `wp_nonce_field` in forms and `check_ajax_referer` in handlers.
- **Storing secrets in plain text** – compromises API keys; always encrypt before saving to database.
- **Using the wrong table prefix** – remember to prepend `$wpdb->prefix` to custom table names.
- **Forgetting to sanitize inputs** – opens doors to SQL injection or XSS; use `sanitize_text_field`, `intval`, `wp_kses_post` as appropriate.
- **Enqueueing assets on every admin page** – causes conflicts and performance degradation; restrict to your plugin’s pages.
- **Not handling n8n webhook failures** – implement retry logic and log errors to aid debugging.
- **Assuming a single site** – if the plugin is used on multisite, use appropriate functions like `is_plugin_active_for_network` and store options per site if needed.
- **Overlooking WP‑CLI compatibility** – avoid `echo` or `print` in constructors; use WP‑CLI friendly output.

## References

- [WordPress Plugin Handbook](https://developer.wordpress.org/plugins/)
- [Composio API Documentation](https://docs.composio.dev)
- [n8n Workflow Documentation](https://docs.n8n.io)
- [OpenRouter API Reference](https://openrouter.ai/docs)

