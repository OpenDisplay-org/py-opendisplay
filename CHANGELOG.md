# Changelog

## [1.0.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v0.3.0...v1.0.0) (2026-01-09)


### ⚠ BREAKING CHANGES

* **connection:** Removed get_device_lock from public API. The global per-device lock mechanism has been removed in favor of simpler single-instance usage pattern.

### Features

* **connection:** integrate bleak-retry-connector for reliable connections ([088c187](https://github.com/OpenDisplay-org/py-opendisplay/commit/088c187c32e6b6564ef5d12184dbe57976e60cf7))

## [0.3.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v0.2.1...v0.3.0) (2025-12-30)


### Features

* add sha to firmware version parsing ([a47d58e](https://github.com/OpenDisplay-org/py-opendisplay/commit/a47d58e07d20b232b65b56d74edef64477497a37))


### Bug Fixes

* fix compressed image upload with chunking ([5d1b48a](https://github.com/OpenDisplay-org/py-opendisplay/commit/5d1b48a3ce8e7fae27526fa1d7495f81ef0bd65d)), closes [#5](https://github.com/OpenDisplay-org/py-opendisplay/issues/5)


### Documentation

* add git commit SHA documentation ([0e2ef50](https://github.com/OpenDisplay-org/py-opendisplay/commit/0e2ef50b7b813e87aceaa7620e7759325dcce0e7))

## [0.2.1](https://github.com/OpenDisplay-org/py-opendisplay/compare/v0.2.0...v0.2.1) (2025-12-30)


### Bug Fixes

* correct advertisement data ([ec152ba](https://github.com/OpenDisplay-org/py-opendisplay/commit/ec152ba53ec7c543957db2b6f618f4485c927b68))


### Documentation

* improve README.md ([e90a612](https://github.com/OpenDisplay-org/py-opendisplay/commit/e90a6128fe20b1bbbfcbaa0b303c72e8ab5359d8))

## [0.2.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v0.1.1...v0.2.0) (2025-12-29)


### Features

* add more dithering algorithms ([1b2fc6a](https://github.com/OpenDisplay-org/py-opendisplay/commit/1b2fc6aeef3ef6c3b81e0c23855d38a61e00a62b))

## [0.1.1](https://github.com/OpenDisplay-org/py-opendisplay/compare/v0.1.0...v0.1.1) (2025-12-29)


### Bug Fixes

* add conftest ([673db99](https://github.com/OpenDisplay-org/py-opendisplay/commit/673db99bfa85608a2d5bcdea1a36d37b25e76b51))

## 0.1.0 (2025-12-29)


### Features

* add discovery function ([2760ef9](https://github.com/OpenDisplay-org/py-opendisplay/commit/2760ef913440b8689bdc6c39d09050fc5f757b64))

## 0.1.0 (2025-12-29)

### Features

* Initial release of py-opendisplay
* BLE device discovery with `discover_devices()` function
* Connect by device name or MAC address
* Automatic image upload with compression support
* Device interrogation and capability detection
* Image resize warnings for automatic resizing
* Support for multiple color schemes (BW, BWR, BWY, BWRY, BWGBRY, GRAYSCALE_4)
* Firmware version reading
* TLV config parsing for OpenDisplay protocol

### Documentation

* Quick start guide with examples
* API documentation
* Image resizing behavior documentation
