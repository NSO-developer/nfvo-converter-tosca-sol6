# SolCon Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project (tries to) adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Virtual compute desc to VDUs
- Default instantiation level to df
- Management field to internal connection points that are assigned as management
- Basic unit conversion (MB to GB only currently)
- Specifying a vim_flavor variable value in the TOSCA config file will cause the value to be read and used instead of 
the variable name
- Updated version of Sol6 models are now supported
- Cisco internal connection points now have interface IDs
- Prerequisite install script added in tools/setup-script.sh

### Fixed
- Logging not getting logs from all modules
- Bug where program expected all vim_flavors to be inputs
- Virtual link mapping to external connection points only when specified

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
