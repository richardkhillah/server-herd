from collections.abc import Sequence


_COLUMNS = (
    ("SERVER", 8),
    ("PORT", 5),
    ("STATUS", 11),
    ("UPTIME", 8),
    ("CLIENTS", 7),
)

_GAP = '  '


def _pad(row: list[str]) -> str:
    padded_fields = [
        f"{field:<{width}}" for field, (_, width) in zip(row, _COLUMNS, strict=True)
    ]
    return _GAP.join(padded_fields)


def _format_uptime(serving: bool, now: float, started_at: float | None) -> str:
    if not serving or started_at is None:
        return '-'
    hours, remainder = divmod(int(now - started_at), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


def render_dashboard(rows: Sequence, now: float) -> list[str]:
    """status rows from Herd.snapshot()"""
    total_width = sum(width for _, width in _COLUMNS) + (len(_COLUMNS) - 1) * len(_GAP)
    lines = [
        "Herd Status".center(total_width),
        _pad([c for c, _ in _COLUMNS])
    ]
    serving_count = 0
    unique_clients = set()
    for status_row in rows:
        uptime = _format_uptime(status_row.serving, now, status_row.started_at)
        client_count = len(status_row.clients)
        lines.append(_pad([
            status_row.name,
            str(status_row.port),
            'serving' if status_row.serving else 'stopped',
            uptime,
            str(client_count)
        ]))
        serving_count += 1 if status_row.serving else 0
        unique_clients.update(status_row.clients)
    lines.append(_pad(
        ['',
         '',
         f'{serving_count}/{len(rows)} serving',
         '',
         f'{len(unique_clients)}']
    ))
    return lines
