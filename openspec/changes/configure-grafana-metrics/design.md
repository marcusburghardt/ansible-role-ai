## Context

The opencode-metrics plugin (https://github.com/marcusburghardt/opencode-metrics)
writes session metrics to a SQLite database with a dimensional schema:
sessions (dimensions), measurements (facts keyed by session_id +
metric_name), projects, and metric_definitions. Timestamps are stored as
Unix epoch milliseconds (INTEGER). The database uses WAL mode for
concurrent read/write safety.

The frser-sqlite-datasource Grafana plugin
(https://github.com/fr-ser/grafana-sqlite-datasource) enables Grafana to
query SQLite databases directly. It supports file-based provisioning for
both datasource configuration and dashboards.

## Goals / Non-Goals

**Goals:**

- Deploy a helper script that starts/stops an ephemeral Grafana container
  with podman, pre-configured to query the opencode-metrics database
- Provision a SQLite datasource pointing to metrics.db automatically
- Ship a pre-built dashboard with 9 panels covering cost, tokens, cache,
  classification, duration, and project breakdowns
- Support on-demand usage -- user starts Grafana when needed, stops when
  done; no persistent systemd service
- Persist Grafana state (annotations, preferences) across start/stop
  cycles via a named podman volume

**Non-Goals:**

- Installing podman -- assumed present on the target system
- Installing or configuring the opencode-metrics plugin itself -- handled
  separately (manual install or future role integration)
- Production Grafana deployment with auth, TLS, or multi-user support
- Alerting configuration -- metrics are for personal analytics
- Supporting docker as an alternative to podman

## Decisions

### Decision 1: Ephemeral container with named volume

**Choice**: Use `podman run` with a named volume
(`opencode-grafana-data`) for Grafana's /var/lib/grafana directory.
The helper script's `stop` subcommand removes the container but
preserves the volume.

**Rationale**: The container is disposable -- Grafana configuration comes
from provisioning files mounted from the host, not from Grafana's
internal database. The named volume preserves user preferences,
annotations, and dashboard modifications between restarts without
requiring a systemd service.

**Alternatives considered**:
- *Systemd service*: Overkill for on-demand personal analytics. Wastes
  resources when not in use.
- *No volume*: Dashboard customizations lost on every restart. Poor UX.

### Decision 2: GF_INSTALL_PLUGINS for the SQLite plugin

**Choice**: Install frser-sqlite-datasource via the `GF_INSTALL_PLUGINS`
environment variable at container startup.

**Rationale**: Avoids building a custom Grafana image. The plugin is
downloaded once and cached in the named volume. Subsequent starts reuse
the cached plugin (Grafana skips already-installed plugins).

**Alternatives considered**:
- *Custom Dockerfile*: More complex, requires image registry or local
  builds. Not justified for a single plugin.
- *Pre-download and bind-mount*: Fragile -- plugin binary format varies
  by Grafana version.

### Decision 3: Anonymous admin access, no login

**Choice**: Set `GF_AUTH_ANONYMOUS_ENABLED=true` and
`GF_AUTH_ANONYMOUS_ORG_ROLE=Admin` to bypass the Grafana login screen.

**Rationale**: This is a local-only, single-user development tool bound
to localhost. Authentication adds friction with no security benefit.
Admin role allows editing dashboards and datasources without restriction.

### Decision 4: Port 3033 to avoid conflicts

**Choice**: Bind to port 3033 instead of the Grafana default 3000.

**Rationale**: Port 3000 conflicts with common development services
(Rails, Create React App, other Grafana instances). Port 3033 is
memorable (Grafana "33") and unlikely to conflict.

### Decision 5: Mount the metrics directory, not the file

**Choice**: Bind-mount `~/.local/share/opencode-metrics/` as a
directory to `/data/metrics/` in the container.

**Rationale**: SQLite WAL mode creates companion files (.db-wal,
.db-shm) alongside the main database file. Mounting the directory
ensures Grafana's SQLite plugin sees all three files for consistent
reads. Mounting only the .db file would miss WAL state, causing stale
or inconsistent query results.

### Decision 6: Epoch milliseconds to seconds conversion in queries

**Choice**: All dashboard queries divide timestamp columns by 1000
(e.g., `recorded_at/1000`) and use the SQLite plugin's "number"
time format (unix epoch seconds).

**Rationale**: The opencode-metrics plugin stores timestamps as Unix
epoch milliseconds (matching JavaScript's Date.now()). The Grafana
SQLite plugin expects epoch seconds for time series. The division is
done in SQL to keep the datasource configuration simple.

### Decision 7: Provisioning directory on the host

**Choice**: Deploy provisioning files to
`~/.config/opencode/grafana/provisioning/` and dashboard JSON to
`~/.config/opencode/grafana/dashboards/`.

**Rationale**: Keeps all OpenCode-related configuration under the
existing `~/.config/opencode/` tree that the role already manages.
The provisioning directory is bind-mounted into the container at
`/etc/grafana/provisioning/`. The dashboard directory is bind-mounted
at `/var/lib/grafana/dashboards/`.

## Risks / Trade-offs

- **Risk**: Grafana container image pulls may be slow on first start
  (and the SQLite plugin install adds ~10s). **Mitigation**: The named
  volume caches both. Subsequent starts are fast (<5s).
- **Risk**: metrics.db may not exist when the user first starts Grafana
  (plugin not yet installed or no sessions completed). **Mitigation**:
  The helper script checks for the database file and prints a helpful
  message if missing.
- **Risk**: podman not installed on non-Fedora/RHEL systems.
  **Mitigation**: The task does not install podman. The helper script
  checks for podman and exits with a clear error if missing.
- **Trade-off**: Dashboard JSON is a static file deployed by the role,
  not generated dynamically. Users who want custom panels must edit the
  JSON or modify dashboards in Grafana (persisted in the named volume).
  This is acceptable for a v1 -- dynamic dashboard generation is
  overengineering for personal analytics.
