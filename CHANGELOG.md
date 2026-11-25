# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `python herd.py` runs all five servers in one process and shows a live status table.
- `--refresh` sets the seconds between redraws (default 1.0, minimum 0.1).
- Automated tests for the server, the herd and the console. Four known bugs are marked as expected failures.
- `requirements.txt` with pinned dependencies.

### Changed

- The places API key is read from `PLACES_API_KEY`, in the environment or `.env`, instead of an `env.py` module.
- The server table and neighbor links moved to `topology.py`.

### Removed

- The `seas_herd` port table.
- `Makefile`, which built the class submission.
