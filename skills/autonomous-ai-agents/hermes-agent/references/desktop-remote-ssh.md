# Connect Hermes Desktop to a remote Hermes over SSH

Use when the desktop app must drive an agent that runs on another machine (a VPS that stays on when the local PC doesn't). No public port, no reverse proxy, no exposed token — the app opens its own SSH tunnel and starts the remote backend.

## Why SSH, not "Remote gateway"

The desktop app supports four connection kinds (`Settings → Gateways → Add connection`):

| Kind | Transport | Auth | When |
|------|-----------|------|------|
| Local | app-spawned backend on this machine | automatic | default |
| **SSH** | app tunnels over SSH | SSH key + app-adopted token | **preferred for a VPS** — nothing exposed |
| Remote gateway | HTTP(S) to a running `hermes serve` | session token or OAuth | needs the port reachable |
| Hermes Cloud | Nous Portal | portal sign-in | hosted instances |

"Remote gateway" needs `hermes serve --host 0.0.0.0 --port 9119` plus firewall + TLS + a pinned `HERMES_DASHBOARD_SESSION_TOKEN`. SSH avoids all of it — pick SSH unless the backend is already behind a reverse proxy.

## Steps

### 1. Make SSH work non-interactively from the desktop machine

The app shells out to `ssh`; a key passphrase prompt or a non-standard port will silently break it. Add an alias to `~/.ssh/config` (Windows: `C:/Users/<user>/.ssh/config`):

```
Host vps-hermes
    HostName <ip>
    Port <port>          # e.g. 2222 — non-22 ports MUST be here
    User root
    IdentityFile C:/Users/<user>/.ssh/<key>
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Verify with `ssh -o BatchMode=yes vps-hermes "echo OK"` — it must print without prompting. `BatchMode=yes` is the point: any prompt means the app will hang.

### 2. Confirm the remote has the serve backend

```bash
ssh vps-hermes "hermes --version; hermes serve --status"
```

`hermes serve` is the JSON-RPC/WebSocket backend the desktop dials. If `serve` is missing the runtime is too old — `hermes update` on the remote. `--ssh-session-token-file` / `--ssh-owner-nonce` in `hermes serve --help` confirm the SSH connection kind is supported. Do NOT start `hermes serve` by hand for an SSH connection; the app starts it and adopts the token.

### 3. Add the connection in the GUI (the user does this)

`Settings → Gateways → Add connection → SSH`, then:

- **Name**: any unique label (`VPS`)
- **SSH host**: the alias (`vps-hermes`) — or paste `root@194.127.192.52:2222` / `ssh root@...`; the app strips the `ssh ` prefix, splits `user@`, and reads the trailing `:port`
- **Key path**: only if not already in `~/.ssh/config`

Same page is reachable via the plug button at the end of the sidebar profile rail, or `Cmd/Ctrl+K → Gateways`.

## Pitfalls

- **This step cannot be scripted.** The app owns `%APPDATA%/Hermes/connections.json` and rewrites it on exit; editing it while the app runs is lost or corrupts the registry. Verify with `cat connections.json` (shape: `{version, primary, launchMode, lastUsed, connections:[{id,kind,label}]}`) but make the change in the UI.
- **An alias created after the app launched isn't in the suggestion list** until the app re-reads `~/.ssh/config` — restart the app (or reopen the dialog) first.
- **The old `connection.json` is legacy.** Multi-gateway lives in `connections.json`; don't write `mode: "ssh"` into the legacy file and expect it to win.
- **SSH is connect-on-demand.** An undialed SSH connection reports `profiles: ['default'], error: 'connect-on-demand'` — the profile list is populated after the first dial, not a failure.
- **Cron/kanban visibility is per-machine.** Connecting Desktop to the VPS shows the VPS's jobs, not the local machine's. Two installs = two independent cron databases; pick one as production and keep scheduled work there.
