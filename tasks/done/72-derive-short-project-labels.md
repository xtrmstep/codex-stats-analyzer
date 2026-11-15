## Title

Derive short project labels from existing identifiers

## Specification

Follow the [project label rules](../specification/01-screens/010-navigation.md#project-labels). This task prepares the shared labels for tasks 73 and 74.

## Work

- Add a small display helper in [`src/internal/ui`](../src/internal/ui) that takes the project keys and source working directories in `StatsCalculation.rows`. Return one entry per known key with the short label and full identifier. For Git, use the stored normalized repository identifier as the full value. For folder-based keys, use the recorded working path that normalizes to that key when available. Leave project attribution, stored keys, and database schema unchanged.
- Derive the base label from the last meaningful component. Handle HTTPS and `ssh://` URLs, SCP-style remotes such as `git@host:team/tools.git`, drive and UNC paths, and POSIX paths. Distinguish a Windows drive prefix from SCP syntax. Ignore trailing separators and omit `.git` only for repositories. Use a readable root or share name when the path has no final folder.
- Resolve collisions from the full project list, case-insensitively and independently of row order. Prefer the shortest distinguishing parent or organization context, then host, share, or drive as needed. Use a deterministic short suffix if the qualifiers still collide. Reserve **Unknown** for missing attribution. Keep qualifiers compact and leave the full identifier for **Project details**.

## Acceptance Criteria

- HTTPS, SSH, and SCP remotes and Windows, UNC, and POSIX folders yield compact labels. A local folder named `notes.git` keeps its suffix. Trailing separators and root paths produce usable labels.
- Multiple checkout paths for the same Git key produce one entry. Different projects sharing a leaf name receive distinct labels, as does a project named `Unknown`. The mapping is the same when input rows arrive in a different order.
