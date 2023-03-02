# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Ability to loading data from a specified commit ID
- Mixins to access the parent and root of a parameter data object (`ParentMixin` and
  `RootMixin`)

### Changed

- Replaced `CommitNotFoundError` with built-in `IndexError`

## [0.1.0] (Feb 24 2023)

### Added

- Parameter data classes (`Param` and `Struct`)
- Database class `ParamDB` to store parameters in a SQLite file
- Ability to retrieve the commit history as `CommitEntry` objects

[unreleased]: https://github.com/PainterQubits/paramdb/compare/v0.1.0...main
[0.1.0]: https://github.com/PainterQubits/paramdb/releases/tag/v0.1.0
