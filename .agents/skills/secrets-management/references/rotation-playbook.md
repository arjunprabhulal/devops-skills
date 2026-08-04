# Rotation Playbook

Two situations need different playbooks. Scheduled rotation is a planned change you control
end to end. A leaked secret is an incident where the wrong action first costs you the most
time. Confusing the two — treating a leak like a calm scheduled rotation, or treating routine
rotation like a fire drill — is how either one goes wrong.

## Contents

- A. Scheduled rotation without downtime: the dual-key overlap
- B. Leaked-secret emergency response: the order matters

## A. Scheduled rotation without downtime: the dual-key overlap

The failure mode of naive rotation is a single moment where the old credential is gone and the
new one hasn't reached every consumer yet — every reader that hasn't picked up the new value
starts failing at once. The fix is to make two credentials valid at the same time, so rotation
is a gradual handover instead of a cutover.

**Steps:**

1. **Issue the new credential alongside the old one.** Both must authenticate successfully at
   this point. Do not touch the old one yet.
2. **Deploy readers that accept both.** Every service that verifies the secret (not just the
   one that uses it to authenticate outbound) needs to accept old-or-new before anything starts
   writing with the new value. This is the step people skip, and it's the one that prevents the
   outage.
3. **Switch writers to the new credential.** Once every reader accepts both, flip the
   producers/callers over. Watch error rates per consumer, not just in aggregate — one
   straggler service still on the old value will show up here first.
4. **Confirm zero usage of the old credential**, then retire it. Don't retire on a timer;
   retire on evidence (access logs show nothing authenticating with the old key/version for a
   full traffic cycle, including batch and weekly jobs).

**How this maps by credential type:**

- **Database passwords**: most managed DBs (RDS, Cloud SQL) support two active users or a
  password history depth > 1. Create `app_user_v2` with the same grants as `app_user_v1`,
  update app config to try v2 then fall back to v1 during rollout, cut writers over, drop
  `app_user_v1` once connection logs are clean.
  ```sql
  -- Postgres: keep both roles live during the overlap window
  CREATE ROLE app_user_v2 LOGIN PASSWORD '...';
  GRANT ALL PRIVILEGES ON DATABASE appdb TO app_user_v2;
  -- after cutover and a clean connection-log window:
  DROP ROLE app_user_v1;
  ```
- **API keys**: most providers (Stripe, GitHub, cloud IAM) let you generate a second active key
  before revoking the first — that's the overlap window. Roll the new key to every consuming
  service, confirm via the provider's per-key usage dashboard that the old key has gone quiet,
  then revoke it. Never revoke-then-issue; that reopens the single-moment-of-failure gap.
- **Signing/encryption keys (JWT, TLS, KMS)**: overlap means the verifier trusts both the old
  and new public key (or key ID) while only one signer is active. Publish the new key in the
  JWKS / trust store first, wait for it to propagate to every verifier's cache (respect their
  TTL), start signing with the new key, and only remove the old public key once nothing is
  presenting a signature made with it. For envelope encryption, keep the old KMS key enabled
  (not deleted) until every ciphertext encrypted under it has been re-wrapped — deleting a KMS
  key immediately makes every secret it wrapped unrecoverable.

**Checklist:**

- [ ] New credential issued; old one still valid and unchanged
- [ ] Every reader/verifier deployed and confirmed to accept both
- [ ] Writers switched; per-consumer error rate watched, not just aggregate
- [ ] Access logs show zero use of the old credential across a full traffic cycle
- [ ] Old credential revoked/deleted, not just rotated out of config
- [ ] Rotation recorded with a date, so "never rotated" doesn't quietly become the new default

**Done when:** the old credential fails to authenticate, no service alerted during the
transition, and nobody had to schedule a maintenance window to do it.

## B. Leaked-secret emergency response: the order matters

The order below is not a preference, it's what limits damage. Assessing blast radius before
revoking gives an attacker free run of the credential for the entire investigation. Scrubbing
history before rotating leaves a still-valid key sitting in every fork and clone that already
exists — cleaning the crime scene while the door is still unlocked.

**The order, and why it's this order:**

1. **Revoke or rotate first.** At the source of truth (Vault, Secrets Manager, the provider's
   dashboard, `DROP ROLE`), not by editing a config file that references it. This is the one
   action with a time cost that compounds every minute it's delayed.
   ```bash
   # Example: kill an AWS access key immediately, ask questions after
   aws iam update-access-key --access-key-id AKIA... --status Inactive --user-name svc-deploy
   ```
2. **Assess blast radius from access logs**, now that the credential is dead and can't do
   further damage. Pull the credential's actual usage window — not "when was it created" but
   "when did it last authenticate, from where, and what did it touch." Cloud audit trails
   (CloudTrail, GCP Audit Logs, Vault audit device) and the target system's own access logs
   both matter; a key can be valid for IAM and still show nothing used against the data it
   protects.
3. **Scrub the source**, only after rotation makes the old value worthless to hold onto:
   - **Git history**: `git filter-repo --path <file> --invert-paths` (or BFG) rewrites history;
     coordinate a force-push, since every clone and fork still has the old commits until they
     re-sync. This is cleanup, not containment — it does nothing if run before step 1.
   - **Container images**: rebuild and re-push any image with the secret baked into a layer;
     `docker history` and layer inspection will surface it even if a later layer deletes the
     file. Deprecate/delete the old image tags from the registry, don't just push a new one
     alongside them.
   - **Logs**: purge or redact the secret from log aggregators (it may be indexed, cached, and
     exported to a SIEM well past the log's own retention window) and confirm log-scrubbing
     covers backups, not just the live index.
4. **Add the control that would have caught it.** A leak that repeats the same way is a process
   gap, not bad luck. If it was a commit, that's a pre-commit hook or CI scanner rule (see
   `SKILL.md` section 1) tuned to catch that pattern. If it was a log line, that's a masking
   rule at the source. If it was a long-lived key with no owner, that's a rotation interval
   assigned going forward, per section 4 of the main skill.

**Checklist:**

- [ ] Credential revoked/rotated at the source of truth
- [ ] Old value confirmed dead (an authentication attempt with it fails)
- [ ] Access logs pulled for the credential's actual usage window, all systems it could reach
- [ ] Blast radius written down: what it touched, whether it was actually used maliciously
- [ ] Git history scrubbed and force-pushed, if the leak was a commit
- [ ] Any image layer containing the secret rebuilt and old tags removed from the registry
- [ ] Logs/log backups scrubbed of the secret value
- [ ] A scanner rule, masking rule, or rotation interval added so this leak pattern is caught
      pre-commit or in CI next time, not just cleaned up after
- [ ] Timeline and root cause handed to `incident-response` for the postmortem

**Done when:** the old credential cannot authenticate anywhere, the blast radius is written
down rather than assumed, no copy of the secret remains in reachable history, images, or logs,
and a specific control now exists that would catch this exact leak before merge.
