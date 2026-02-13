# Changelog

## [3.1.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v3.0.0...v3.1.0) (2026-02-13)


### Features

* add typed board manufacturer API and docs ([a79eb8d](https://github.com/OpenDisplay-org/py-opendisplay/commit/a79eb8d9d1c9c2ed440a77930115d6c7b90f84f8))

## [3.0.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.5.1...v3.0.0) (2026-02-11)


### ⚠ BREAKING CHANGES

* add FitMode image fitting strategies (contain, cover, crop, stretch)

### Features

* add FitMode image fitting strategies (contain, cover, crop, stretch) ([786c614](https://github.com/OpenDisplay-org/py-opendisplay/commit/786c6144f6524f75ddb90013fa15c0d06dd1ad7f))

## [2.5.1](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.5.0...v2.5.1) (2026-02-11)


### Bug Fixes

* bump epaper-dithering version ([2dfd846](https://github.com/OpenDisplay-org/py-opendisplay/commit/2dfd8461ae6e02fe3e01c3f5cbf3b22af8b12049))

## [2.5.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.4.0...v2.5.0) (2026-02-11)


### Features

* bump epaper-dithering version and expose tone compression option ([c7d3dd1](https://github.com/OpenDisplay-org/py-opendisplay/commit/c7d3dd1cde26c81883793686e019360741004039))

## [2.4.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.3.0...v2.4.0) (2026-02-09)


### Features

* bump epaper-dithering version to 0.5.1 ([9ff01ba](https://github.com/OpenDisplay-org/py-opendisplay/commit/9ff01bad1620937cac7d671a23037cbfa81451b9))

## [2.3.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.2.0...v2.3.0) (2026-02-04)


### Features

* **epaper-dithering:** bump version for corrected palette ([2a2d5ff](https://github.com/OpenDisplay-org/py-opendisplay/commit/2a2d5ff7a72b7cb49d54ab82581275af591df67f))

## [2.2.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.1.0...v2.2.0) (2026-02-03)


### Features

* **palettes:** add automatic measured palette selection ([ae35b26](https://github.com/OpenDisplay-org/py-opendisplay/commit/ae35b26fd83fcbc65ccd8444fc29b5a258b4e865))

## [2.1.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v2.0.0...v2.1.0) (2026-01-12)


### Features

* add device reboot command (0x000F) ([147371d](https://github.com/OpenDisplay-org/py-opendisplay/commit/147371d617e92e7cf3d425c86608641eeabeea7b))
* **config:** add device configuration writing with JSON import/export ([4665d98](https://github.com/OpenDisplay-org/py-opendisplay/commit/4665d98eccfdc90b419f092f43d0c03a34471860))

## [2.0.0](https://github.com/OpenDisplay-org/py-opendisplay/compare/v1.0.0...v2.0.0) (2026-01-11)


### ⚠ BREAKING CHANGES

* Dithering functionality moved to standalone epaper-dithering package

### Code Refactoring

* extract dithering to epaper-dithering package ([95aa3c1](https://github.com/OpenDisplay-org/py-opendisplay/commit/95aa3c1700cad438b36146443e01f1fb8bcb00f3))

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
