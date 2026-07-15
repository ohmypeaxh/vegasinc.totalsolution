# Cumulative update policy

Incremental updates are intentionally deferred until after the first production
release. When the updater is introduced, every small update package must be
**cumulative** rather than dependent on a particular earlier patch.

## Required behaviour

- A package for version `1.0.5` contains all application changes introduced by
  `1.0.1` through `1.0.5`.
- The updater checks the installed version, but the user does not need to install
  intermediate update packages in order.
- Installing the current cumulative package on any supported earlier version
  produces the same files and configuration migrations as a sequential update.
- The manifest declares the package version, minimum supported base version,
  file hashes, files to add or replace, safe removals, and ordered migrations.
- Each manifest and payload is cryptographically signed and verified before any
  installed file is changed.
- Updates stop the running application, stage files outside the installation
  directory, verify hashes, replace files atomically, and retain a rollback copy.
- User configuration, credentials, projects, and generated documents are never
  overwritten. Configuration migrations are idempotent and versioned.
- If the installed base is older than the declared minimum, or if Python/Qt or
  another foundational runtime dependency changes incompatibly, the updater
  directs the user to the full installer instead of applying a risky patch.

## Package model

The first release remains a full installer. Later releases may provide both:

1. a full installer for clean installations and unsupported old versions; and
2. a smaller cumulative update package for all supported installed versions.

The update package may reuse unchanged files from the existing PyInstaller
one-folder installation. Changed application modules, plugins, resources, and any
changed runtime files are included in the latest package, regardless of which
earlier patch first introduced them. This keeps each update self-contained while
avoiding redistribution of the entire application when the runtime is unchanged.

