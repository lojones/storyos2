# Database Migrations

This directory contains database migration scripts for StoryOS.

## Running Migrations

### Add Version Field Migration

This migration adds the `version` field to all existing game sessions for optimistic locking support.

```bash
python -m backend.migrations.add_version_field
```

This should be run once after deploying the optimistic locking changes.

## What is Optimistic Locking?

Optimistic locking prevents race conditions and lost updates when multiple processes try to update the same document simultaneously. It works by:

1. Each document has a `version` field that increments on every update
2. When reading a document, we capture the current version
3. When updating, we only succeed if the version hasn't changed
4. If the version changed (another process updated it), we retry with the new version

This ensures that concurrent updates don't overwrite each other's changes.

## Implementation Details

- Version field is initialized to 1 for new documents
- Updates use MongoDB's atomic `$inc` operator to increment version
- If a version conflict is detected, updates retry up to 3 times with exponential backoff
- All game session updates (both full document and field-level) use this mechanism
