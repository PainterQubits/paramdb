# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Ability to specify start and end indices in `ParamDB.commit_history()`
- Support for scalar [`astropy.units.Quantity`] objects

### Changed

- `ParamDict` can be initialized from keyword arguments in addition to dictionaries
- Parameter dataclass bases (`Param` and `Struct`) automatically convert subclasses into
  dataclasses, so the `@dataclass` decorator should no longer be used

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

[unreleased]: https://github.com/PainterQubits/paramdb/compare/v0.2.0...main
[0.2.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.2.0
[0.1.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.1.0
[`astropy.units.quantity`]: https://docs.astropy.org/en/stable/api/astropy.units.Quantity.html#astropy.units.Quantity
