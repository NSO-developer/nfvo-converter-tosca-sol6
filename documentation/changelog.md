# SolCon Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project (tries to) adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Logging not getting logs from all modules
- Bug where program expected all vim_flavors to be inputs


## [0.2.1]
### Added
- Interactive mode (access with -i)

## [0.2.0]
### Added
- Nokia provider options
- Can now not include value that is expected in configuration file, it'll be skipped

### Changed
- Split TOSCA and SOL6 configuration files
- Hardened the program against more crashes
- Reworked how the internals of the program worked completely, it's now much easier to extend and 
override things in the python 

## [0.1.0]
- Initial release
