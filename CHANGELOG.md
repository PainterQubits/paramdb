# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.0] (Jan 31 2024)

### Added

- `ParamDB.load_commit_entry()` loads a commit entry by ID or the most recent commit.
- `ParamDB.commit_history_with_data()` to retrieve the commit history with data.
- `CommitEntryWithData` to store a commit entry containing data.

### Changed

- `ParamDB.commit()` returns a `CommitEntry` instead of the commit ID.

### Removed

- `ParamDB.latest_commit` is replaced by `ParamDB.load_commit_entry()`

## [0.10.2] (Dec 5 2023)

### Changed

- Change supported Python versions from `>=3.9,<3.13` to `^3.9` for better compatibility
  with other Poetry projects and future versions of Python.

## [0.10.1] (Nov 6 2023)

### Added

- Support for Python 3.12

## [0.10.0] (Aug 30 2023)

### Added

- Support for Python 3.9

### Removed

- Parameter dataclass bases (`Param` and `Struct`) no longer set `kw_only` to True by
  default (since this feature does not exist in Python 3.9).

## [0.9.1] (Aug 9 2023)

### Changed

- Custom `ParamData` subclasses have an improved error message if extra keyword arguments
  are passed.

## [0.9.0] (June 29 2023)

### Added

- `ParamDB.path` to retrieve the database path.
- `ParamDB.latest_commit` to retrieve the latest commit entry.

## [0.8.0] (June 9 2023)

### Changed

- Documentation website moved to Read the Docs.

### Added

- Badges for latest PyPI version, license, CI status, Codecov, and docs website build.

## [0.7.0] (May 19 2023)

### Changed

- `ParamDB.commit()` returns the ID of the newly created commit.
- `ParamDB.load()` converts `datetime` objects to local time regardless of the timezone
  stored internally in the database.

## [0.6.0] (May 3 2023)

### Added

- `ParamDB.dispose()` function for cases where it is required to fully clean up the
  database before the program ends, such as in testing suites.

### Changed

- Commits get the current time in a way that can be mocked in tests where we
  want to control the time.

## [0.5.0] (Apr 11 2023)

### Changed

- `datetime` objects (currently used in `CommitEntry.timestamp` and
  `ParamData.last_updated`) are timezone-aware.
- If ParamDB `load_classes` parameter is False, `datetime` and Astropy `Quantity`
  objects are not loaded either.

## [0.4.0] (Mar 28 2023)

### Added

- ParamDB `load_classes` parameter can be set to False to load parameter data classes as
  dictionaries (created to allow ParamView to access data)
- Keys for special properties in dictionary representations of parameter data can be
  imported
- ParamDict returns keys in `__dir__()` so that they are suggested by interactive prompts
  like IPython.

### Changed

- ParamDict uses dict_keys, dict_values, and dict_items instead of default KeysView,
  ValuesView, and ItemsView since they print nicely

## [0.3.0] (Mar 14 2023)

### Added

- Ability to specify start and end indices in `ParamDB.commit_history()`
- Support for scalar `astropy.units.Quantity` objects
- Parameter dataclass bases (`Param` and `Struct`) automatically convert subclasses into
  dataclasses `kw_only` as True by default

### Changed

- `ParamDict` can be initialized from keyword arguments in addition to dictionaries

## [0.2.0] (Mar 8 2023)

### Added

- Ability to specify commit ID in `ParamDB.load()`
- `ParamData.parent` and `ParamData.root` properties
- Mixins `ParentType[PT]` and `RootType[PT]` to type cast parent and root
- Parameter collection classes `ParamList` and `ParamDict`
- Database now ignores dataclass fields where `init` is `False`

### Removed

- `CommitNotFoundError` (replaced with built-in `IndexError`)
- Private `_last_updated` dataclass field in parameter dataclasses

## [0.1.0] (Feb 24 2023)

### Added

- Parameter data base class `ParamData`
- Parameter dataclass bases (`Param` and `Struct`)
- Database class `ParamDB` to store parameters in a SQLite file
- Ability to retrieve the commit history as `CommitEntry` objects

[unreleased]: https://github.com/PainterQubits/paramdb/compare/v0.11.0...develop
[0.11.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.11.0
[0.10.2]: https://github.com/PainterQubits/paramdb/releases/tag/v0.10.2
[0.10.1]: https://github.com/PainterQubits/paramdb/releases/tag/v0.10.1
[0.10.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.10.0
[0.9.1]: https://github.com/PainterQubits/paramdb/releases/tag/v0.9.1
[0.9.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.9.0
[0.8.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.8.0
[0.7.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.7.0
[0.6.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.6.0
[0.5.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.5.0
[0.4.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.4.0
[0.3.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.3.0
[0.2.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.2.0
[0.1.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.1.0
