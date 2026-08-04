# Worked Example: Splitting `full_name` into `first_name` / `last_name`

The scenario: a `users` table has a single `full_name` text column. The application needs
`first_name` and `last_name` as separate fields — for sorting, for a "Hi, Arjun" greeting, for
an export that a downstream system expects split. There is no maintenance window, the table has
production traffic on it right now, and the old and new code must both be correct at every point
in the rollout. That's expand-then-contract end to end, with real SQL at each phase.

## Contents

- Phase 1: Expand
- Phase 2: Backfill
- Phase 3: Migrate reads (dual-write stays on)
- Phase 4: Verify
- Phase 5: Contract

## Phase 1: Expand

Add the new columns, nullable, with no application code depending on them yet.

```sql
ALTER TABLE users ADD COLUMN first_name text;
ALTER TABLE users ADD COLUMN last_name text;
```

Nullable and unindexed on purpose — a pure additive change that ships without locking existing
rows or requiring every row to already have a value. Next, add a trigger so any new write to
`full_name` also populates the split columns, keeping new rows consistent going forward without
touching application code:

```sql
CREATE OR REPLACE FUNCTION sync_name_split() RETURNS trigger AS $$
BEGIN
  NEW.first_name := split_part(NEW.full_name, ' ', 1);
  NEW.last_name  := NULLIF(substring(NEW.full_name FROM position(' ' IN NEW.full_name) + 1), '');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_name_split
  BEFORE INSERT OR UPDATE OF full_name ON users
  FOR EACH ROW EXECUTE FUNCTION sync_name_split();
```

**Deploy note:** ships alone, nothing else in the same release. Old application code still reads
and writes only `full_name` and has no idea the new columns exist.

**Rollback:** `DROP TRIGGER trg_sync_name_split ON users;` and drop the two columns. No
application code references them yet, so there is nothing else to unwind.

## Phase 2: Backfill

The trigger only covers rows written from now on. Every existing row still has `first_name` and
`last_name` as `NULL`. Backfill them in small batches, not one table-wide `UPDATE`.

```sql
-- One batch: claim up to 5000 unbackfilled rows by id range, commit, repeat.
UPDATE users
SET first_name = split_part(full_name, ' ', 1),
    last_name  = NULLIF(substring(full_name FROM position(' ' IN full_name) + 1), '')
WHERE id BETWEEN :batch_start AND :batch_start + 4999
  AND first_name IS NULL
  AND full_name IS NOT NULL;
```

Drive it from a small script or job, not a single psql session, tracking progress in a table:

```sql
CREATE TABLE backfill_progress (job_name text PRIMARY KEY, last_id bigint NOT NULL);
```

Each batch commits independently, then updates `last_id` and sleeps briefly (100-500ms,
depending on observed replication lag and query latency) before the next batch. On restart, the
job reads `last_id` and continues — no re-scan, no double-processing, because the
`WHERE first_name IS NULL` guard makes every batch idempotent even if a batch is retried.

**Deploy note:** the backfill job is its own deploy, separate from any application change, and
can run for hours or days at low priority.

**Rollback:** stop the job. Rows already backfilled are correct and harmless to leave as-is;
`first_name`/`last_name` are still unread by the application. No data was destroyed, so there is
nothing to restore.

## Phase 3: Migrate reads (dual-write stays on)

Deploy application code that reads `first_name`/`last_name` for display and sorting, while still
writing `full_name` as the source of truth (the trigger keeps the split columns current on every
write). Use a feature flag to control the percentage of read traffic on the new columns — see
`feature-flags` — rather than an all-or-nothing switch. Both code paths must be live: a reader
still on the old flag value falls back to computing the split from `full_name` in application
code, so a flag flip in either direction stays safe.

**Deploy note:** an application deploy, not a schema change — no SQL ships here. It only goes out
once Phase 2's backfill has reached 100%, confirmed by a zero-row count of unbackfilled rows.

**Rollback:** flip the feature flag back to 0%. The old code path (deriving the split from
`full_name` at read time) still works because `full_name` was never touched.

## Phase 4: Verify

Compare old and new before trusting the new columns as the sole source.

```sql
-- Should return zero rows; any result is a real divergence to investigate.
SELECT id, full_name, first_name, last_name
FROM users
WHERE full_name IS NOT NULL
  AND (first_name IS DISTINCT FROM split_part(full_name, ' ', 1)
       OR last_name IS DISTINCT FROM NULLIF(substring(full_name FROM position(' ' IN full_name) + 1), ''));
```

Run this as a recurring check, not a one-off, for the full dual-write period — new writes and
edge cases (a single-word name, extra whitespace, a name change) can introduce divergence after
the initial backfill looked clean. Set a deadline for the verification window; an open-ended
"keep checking" phase is how dual-writes become permanent.

**Rollback:** verification finding divergence isn't a rollback trigger by itself — it's a signal
to fix the trigger or backfill logic and re-run the backfill for affected rows. The read flag
from Phase 3 stays wherever it was; divergence in unread rows doesn't affect production traffic
because the read path defaults to old-code fallback whenever the flag says so.

## Phase 5: Contract

Only after Phase 3 has served 100% of read traffic from the new columns under real load, and
Phase 4's divergence check has run clean for the agreed window, remove the old path.

```sql
-- Stop dual-writing first, before touching the column.
DROP TRIGGER trg_sync_name_split ON users;
DROP FUNCTION sync_name_split();

-- Confirm nothing still reads full_name (app code, ad hoc queries, downstream
-- exports), then rename rather than drop, for one more reversible window:
ALTER TABLE users RENAME COLUMN full_name TO full_name_deprecated;
-- After a defined retention window with no errors and no queries hitting it:
ALTER TABLE users DROP COLUMN full_name_deprecated;
```

**Deploy note:** the trigger removal and the rename/drop are two separate deploys, not one — the
trigger can go the moment dual-writing is confirmed unnecessary, the drop waits for the full
retention window regardless. Renaming instead of dropping outright keeps this phase reversible
for that window; a rename can be undone instantly, a drop cannot.

**Rollback:** if the trigger was already dropped and something unexpected still needed
`full_name`, recreate it from Phase 1 and it starts populating both columns again on the next
write. If the column has been renamed but not dropped, rename it back. Once it's actually
dropped, rollback means restoring from the backup taken before the drop — which is why the drop
is the very last, most deliberate step.
