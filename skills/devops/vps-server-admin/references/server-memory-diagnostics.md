# Memory diagnostics: the OpenLiteSpeed PHP pool & container limits

## Measure PSS, never summed RSS

`ps` RSS counts shared pages (OPcache, shared libraries) once *per process*. Summing RSS across a PHP worker pool therefore multiplies the shared pages by the worker count and reports a figure that can be 2-3x the truth — 26 `lsphp` workers "sum" to ~3.4 GB while actually occupying ~1.3 GB. Quoting the inflated number drives the wrong decision (which component to attack) and has to be retracted in front of the user.

Per-component real memory:

```bash
pss() {  # $1 = process name (comm)
  t=0; n=0
  for p in $(pgrep -x "$1"); do
    v=$(awk '/^Pss:/{s+=$2} END{printf "%d", s}' /proc/$p/smaps_rollup 2>/dev/null)
    [ -n "$v" ] && { t=$((t+v)); n=$((n+1)); }
  done
  echo "$1: $n proses, $((t/1024)) MB"
}
pss lsphp; pss mariadbd
```

PSS splits each shared page among the processes mapping it, so PSS totals are additive and comparable to `free -m`'s "used".

Read `free -m` first. If "available" is a comfortable fraction of total, the box is not the problem regardless of what the RSS sum claims.

## All sites share ONE PHP pool

OpenLiteSpeed routes every `.php` request through a single LSAPI external app:

```
# /usr/local/lsws/conf/httpd_config.conf
extProcessor lsphp{
    type    lsapi
    address uds://tmp/lshttpd/lsphp.sock     # ONE socket for every vhost
    maxConns 10
    env     PHP_LSAPI_CHILDREN=25
}
scriptHandler{ add lsapi:lsphp  php }        # every vhost -> that one pool
```

Consequences:

- **Taking one site offline frees ~0 RAM.** The workers serving it are the same workers serving the others, and they stay warm. Suspending a single site only reduces CPU and attack surface. A box holding four low-traffic WordPress sites sits at roughly the same PHP footprint with one of them down as with all four up.
- The pool is per PHP *version*. Sites on different versions get different pools — check that before reasoning about "the PHP processes".

## Where the worker cap lives

Two places, both relevant:

```bash
grep -rn 'PHP_LSAPI_CHILDREN' /usr/local/lsws/conf/httpd_config.conf             # global ceiling
 grep -rn 'LSAPI_CHILDREN' /www/server/panel/vhost/openlitespeed/detail/*.conf   # per-site override
```

The global `PHP_LSAPI_CHILDREN` is inherited by every vhost and ships high enough (100) that a traffic spike can spawn ~100 workers and OOM a small box. The per-site `LSAPI_CHILDREN` overrides it for that site.

Direction depends on the symptom, and the two are not in conflict:

- `Reached max children process limit ... please increase LSAPI_CHILDREN` in `/usr/local/lsws/logs/stderr.log` with sites 500ing → raise it.
- RAM exhausted after a spike, workers bloated → lower the global ceiling so the worst case is bounded.

Before editing either file, confirm the panel will not regenerate it:

```bash
grep -rn 'PHP_LSAPI_CHILDREN' /www/server/panel/class/ /www/server/panel/class_v2/   # no hits = the edit sticks
```

Back up the config, edit, then `systemctl restart openlitespeed`.

**A restart recycles the pool but does not shrink it.** Workers respawn immediately and PSS returns to roughly where it was — never present a restart as a memory saving. The durable levers are the ceiling and a lower per-process `memory_limit`.

## Container memory limits

Set or change a limit on a running container without recreating it:

```bash
docker update --memory 384m --memory-swap 512m 9router
docker inspect 9router --format '{{.HostConfig.Memory}}'      # bytes; 0 = unlimited
```

`--memory-swap` must be >= `--memory` or the daemon rejects the update; set both. `HostConfig.Memory = 0` means unlimited — the default for anything started without `-m`, and a common cause of a container quietly eating RAM.

Parking an unused service without losing data:

```bash
docker stop n8n                                          # container + named volume preserved, nothing deleted
docker inspect n8n --format '{{.State.Status}}'          # exited
docker volume ls | grep n8n                              # volume still there
docker start n8n                                         # back exactly as it was
```

With `--restart unless-stopped` (the usual policy) an explicitly stopped container **stays stopped across a host reboot** — correct for a service parked on purpose. With `always`, a reboot resurrects it.

State the side effect before parking a service: any vhost reverse-proxying it starts returning **503** (e.g. `n8n.<domain>` once the n8n container is down). That is expected, not breakage, but the user needs to hear it.
