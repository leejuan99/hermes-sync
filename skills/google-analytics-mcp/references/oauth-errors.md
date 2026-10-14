# Common OAuth Errors and Fixes

## Error: `invalid_grant: Token has been expired or revoked.`
- **Cause:** The OAuth token stored by Hermes has expired.
- **Fix:** Re‑run `hermes mcp install google-analytics-mcp` to refresh consent.

## Error: `access_denied: The user did not grant the requested scopes.`
- **Cause:** User clicked “Deny” or skipped granting Analytics Admin/Data API scopes.
- **Fix:** Restart the MCP install and ensure you click **Allow** for all requested scopes.

## Error: `403: Permission denied` when calling MCP tools.
- **Cause:** The authenticated account lacks access to the specified GA4 property.
- **Fix:** Verify that the Google account used in OAuth has at least **Read & Analyze** permission on the property. Ask the property owner to grant access if needed.

## Error: `400: Invalid property format`
- **Cause:** Property ID supplied without `properties/` prefix or with extra characters.
- **Fix:** Use the exact format `properties/<GA4_PROPERTY_ID>` (numeric only).

## General Tips
- Keep the `GOOGLE_APPLICATION_CREDENTIALS` environment variable set to the path of your OAuth client JSON *before* running any `hermes mcp` command.
- If you change the JSON file, repeat the MCP install step to update credentials.
