# Spec Delta

## ADDED Requirements

### Requirement: Capture permission events as an observer
The `opencode-metrics` plugin SHALL record `permission.asked` and
`permission.replied` events in its local database. Capture SHALL be
observer-only: it SHALL NOT approve, reject, delay, or modify a permission
decision, and a capture failure SHALL NOT affect the session or the permission
prompt.

#### Scenario: Permission is asked and answered
- **WHEN** a permission request is shown and the user replies `once`, `always`,
  or `reject`
- **THEN** the plugin SHALL persist one event with both timestamps and the
  reply without changing the outcome

#### Scenario: Capture fails
- **WHEN** the local database is unavailable or a write fails
- **THEN** the session and permission prompt SHALL continue normally and the
  failure SHALL be logged without surfacing as a user error

### Requirement: Expose the permission capture contract
The plugin SHALL expose contract version `1` through a `permission_contract`
marker table and SHALL store events in the `permission_events` table.

#### Scenario: Consumer checks the contract
- **WHEN** the role helper reads `permission_contract`
- **THEN** it SHALL receive version `1` and know that `permission_events` is
  available

### Requirement: Record complete permission event fields
Each row in `permission_events` SHALL include a stable permission identifier,
the session identifier, project identifier, agent, model, action, canonical
resource, resource hash, reply, asked timestamp, replied timestamp, wait
milliseconds, source tool, source message identifier, and the contract version.

#### Scenario: Asked and replied timestamps
- **WHEN** an event is recorded
- **THEN** the row SHALL contain both timestamps and the computed wait duration

#### Scenario: Reply outcome
- **WHEN** the user replies once, always, or reject
- **THEN** the row SHALL store that exact reply value

### Requirement: Deduplicate permission events
The permission identifier SHALL be unique and a repeated event SHALL upsert
rather than duplicate the row.

#### Scenario: Duplicate delivery
- **WHEN** the same permission event is delivered twice
- **THEN** the plugin SHALL keep one row for that permission identifier

#### Scenario: Late reply
- **WHEN** a reply arrives after the ask was recorded
- **THEN** the plugin SHALL update the existing row with the reply, timestamp,
  and wait duration

### Requirement: Canonicalize shell resources at capture time
For shell actions the plugin SHALL store a canonical value containing at most
the command head and one subcommand token. Assignments, quoting, URLs, and paths
SHALL be removed from the canonical value.

#### Scenario: Shell command with arguments
- **WHEN** a shell resource is `git push origin feature/secret-name`
- **THEN** the canonical value SHALL be limited to `git push`

#### Scenario: Shell wrapper with assignment
- **WHEN** a shell resource begins with an environment assignment before the
  command
- **THEN** the assignment SHALL be removed and the canonical value SHALL begin
  at the command head

### Requirement: Canonicalize file and directory resources
For file and directory actions the plugin SHALL store a path class and file
extension rather than the full path.

#### Scenario: File path is requested
- **WHEN** a read permission targets a file under a project directory
- **THEN** the canonical value SHALL describe the project path class and the
  extension without the full path

#### Scenario: External directory is requested
- **WHEN** an external-directory permission targets a home directory path
- **THEN** the canonical value SHALL describe the home path class without the
  full path

### Requirement: Hash raw resources and redact secrets
The plugin SHALL store a salted hash of the raw resource for recurrence
detection and SHALL NOT store secrets, tokens, headers, credentials, or message
text.

#### Scenario: Secret appears in a command
- **WHEN** a shell resource contains an authorization header or token
- **THEN** the stored canonical value SHALL omit the secret and the raw value
  SHALL NOT be stored

#### Scenario: Recurrence detection
- **WHEN** the same raw resource appears in multiple sessions with different
  arguments
- **THEN** the salted hash SHALL allow grouping without storing the raw value

### Requirement: Persist saved permission patterns
When a user replies `always`, the plugin SHALL record the save patterns
returned by the permission event in canonical form. It SHALL distinguish those
patterns from the presented resource so the retrospective can detect broad or
unusable grants.

#### Scenario: Always reply with a saved pattern
- **WHEN** the user replies `always` and the event includes a save pattern
- **THEN** the canonical save pattern SHALL be stored with the event

#### Scenario: Parameterized resource
- **WHEN** an always reply saves a pattern containing variable placeholders or
  one-off arguments
- **THEN** the retrospective SHALL be able to flag it as non-reusable

### Requirement: Provide a friction view
The plugin SHALL expose a read-only view named `v_permission_friction` that
aggregates permission events by action, canonical resource, project, agent, and
model. The view SHALL include prompt count, median and p95 wait, always count,
reject count, first-seen, and last-seen timestamps.

#### Scenario: Aggregated friction
- **WHEN** the role helper queries the view for a project and window
- **THEN** it SHALL receive prompt counts and wait statistics without reading
  individual raw resources

#### Scenario: Empty window
- **WHEN** no permission events exist in the requested window
- **THEN** the view SHALL return no rows and the helper SHALL report the
  absence without error

### Requirement: Apply retention defaults
The plugin SHALL enable permission capture by default with a retention period
of 90 days and SHALL support disabling capture through configuration. The
settings SHALL be `permission_capture.enabled`,
`permission_capture.retention_days`, and `permission_capture.store_raw`. It
SHALL provide a cleanup operation that removes events older than the retention
period.

#### Scenario: Expired events
- **WHEN** the retention period elapses
- **THEN** the cleanup operation SHALL remove expired permission events and
  SHALL leave session-level metrics intact

#### Scenario: Capture disabled
- **WHEN** permission capture is disabled in configuration
- **THEN** the plugin SHALL NOT write permission events and SHALL continue
  recording its existing session metrics

### Requirement: Protect stored permission data
The plugin SHALL store the metrics database with owner-only permissions. Raw
resource storage SHALL be disabled by default and, when enabled explicitly,
SHALL still redact secrets.

#### Scenario: Default storage
- **WHEN** capture is enabled with default settings
- **THEN** raw resources SHALL NOT be stored and the database SHALL be
  owner-readable only

#### Scenario: Raw storage opt-in
- **WHEN** `permission_capture.store_raw` is enabled
- **THEN** stored values SHALL still redact credentials and tokens

### Requirement: Document the backfill limitation
The plugin documentation SHALL state that permission events are ephemeral and
cannot be backfilled, so history begins when capture is enabled. It SHALL
document the contract version, the table and view names, retention, and the
sanitization rules so the role helper can consume them.

#### Scenario: First enablement
- **WHEN** capture is enabled on an existing installation
- **THEN** the documentation SHALL make clear that earlier permission history
  is unavailable and the retrospective starts from the enablement date

### Requirement: Test the capture contract
The plugin test suite SHALL cover event ingestion, duplicate delivery, late
replies, canonicalization, secret redaction, retention cleanup, the friction
view, and fail-open behavior.

#### Scenario: Synthetic event stream
- **WHEN** the tests run
- **THEN** they SHALL use synthetic events and a temporary database and SHALL
  NOT touch the user's metrics database

#### Scenario: Redaction regression
- **WHEN** a synthetic event contains a credential
- **THEN** the test SHALL fail if the credential appears in the stored row or
  the friction view

### Requirement: Remain compatible with role consumers
The plugin SHALL keep the permission tables additive and SHALL NOT rename or
remove existing session metric columns. The role helper SHALL check the contract
version before using permission-specific fields and SHALL fall back to
session-level metrics when the contract is older or absent. Contract changes
that remove or rename fields SHALL increment the version.

#### Scenario: Older plugin
- **WHEN** the role helper finds no permission event table
- **THEN** the retrospective SHALL still run and SHALL label permission
  findings as reduced confidence

#### Scenario: Future contract
- **WHEN** the helper finds a contract version it does not support
- **THEN** it SHALL report the mismatch and SHALL NOT parse unknown fields
