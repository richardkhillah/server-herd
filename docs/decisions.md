# Decision log

Why the project is built the way it is. Bounds, acceptance checks and scope live in the Jira tickets (`HERD-n`) named here.

## Agreed

| # | Decision |
|---|---|
| D1 | **Standalone portfolio project** (2026-11-13). Inspired by the UCLA CS131 proxy-herd assignment, but no longer coursework. |
| D2 | **Readability first** (2026-11-13). Clear names and logical flow are the primary goal, because the code will be shown publicly. |
| D3 | **Geoapify, not Google Places** (2026-11-13). Google now requires payment info. |
| D4 | **One port table** (2026-11-13). The `seas_herd` table goes away; a single table serves the whole project. |
| D5 | **`topology.py` is the only home for ports and neighbors** (2026-11-15). `server.py` and `herd.py` both import it, so they never import each other. |
| D6 | **Messages are newline-terminated lines** (2026-11-15). A connection can carry several, so the servers work interactively with `nc`. |
| D7 | **Servers flood the same `AT` line the client gets** (2026-11-15). No visited list. This leaves one message format, and the original server's name survives every hop. |
| D8 | **Flooding stops by timestamp** (2026-11-15). A server stores and forwards a location only when its timestamp is newer than the stored one, so a duplicate stops at the first server that has it. |
| D9 | **A stale `IAMAT` is answered, not stored** (2026-11-15). The reply is the `AT` line built from the message just received. It isn't stored or flooded, and it's logged. |
| D10 | **`WHATSAT` radius and limit start at 1, not 0** (2026-11-15). Geoapify rejects 0 for both. Bounds: HERD-8. |
| D11 | **Store, flood, then reply** (2026-11-15). Neighbors are sent to one at a time, before the client gets its reply. |
| D12 | **The herd never tells a server how to behave** (2026-11-15). It sets up, starts, monitors, stops and restarts servers. So no places-lookup function is passed into `Server` or `Herd`. |
| D13 | **Places settings come only from the environment** (2026-11-15). `FAKE_PLACES=1` picks the sample file; the planned `--fake-places` flags are dropped. Values: HERD-12, HERD-13. |
| D14 | **Bad settings stop startup** (2026-11-15). Both entry points call `places.check_settings()`, which exits with a clear message. |
| D15 | **A Geoapify failure replies `? <line>`** (2026-11-15). A client error, a non-200 status or a timeout all get the exact line received back, and the reason is logged. |
| D16 | **`sample_places.json` sits next to `places.py`** (2026-11-15). The app reads it under `FAKE_PLACES=1`, not only the tests. Fine for now. |
| D17 | **All servers run in the herd's process** (2026-11-15). One asyncio event loop. Separate processes may come later. |
| D18 | **A leading underscore means nothing outside uses it** (2026-11-15). Applies to classes and modules. `Herd`'s attributes are private, and `Server` offers `stop()` and `is_serving()` so `_server` stays private. |
| D19 | **`Herd.snapshot()` returns frozen copies** (2026-11-15). The table is drawn from `ServerStatus` rows, not from the herd, so drawing can't change anything. |
| D20 | **The console calls only `Herd`'s public methods** (2026-11-15). Plain method calls, no broker. It knows nothing about servers. |
| D21 | **`Herd.stop_server()` and `start_server()` return nothing** (2026-11-15). Command–query separation; repeating one is a no-op. The console writes all the wording. |
| D22 | **Commands return `ShowLine`, `ShowPage` or `Quit`** (2026-11-15). Renamed because "message" means only a protocol line. |
| D23 | **Long output opens in `less`, short results use one line** (2026-11-15). Works like `git log`: `q` returns to the table. Confirmations and errors never open the pager. |
| D24 | **The console reads stdin with `loop.add_reader`** (2026-11-15). No `asyncio.Protocol` class. |
| D25 | **Plain ANSI escape codes** (2026-11-15). No new Python dependency for the display. |

## Open

| # | Question |
|---|---|
| O1 | **Console state.** Where does the console keep its state (the paused flag, the reader)? Decide in HERD-25. Proposal: local variables inside `run_console`. |
| O2 | **Minimum terminal size.** What shows when the window is smaller than the table? Decide in HERD-29. Proposal: one line such as "window too small: need 47×10". |
| O3 | **Redraw after resize.** When is the table redrawn? Decide in HERD-29. Proposal: immediately on SIGWINCH, independent of `--refresh`. |
| O4 | **Herd-mode log files.** HERD-21 says "log files stay"; the code writes one `herd.log`, which was an assumption. Is one file right? |

Closed: none yet.
