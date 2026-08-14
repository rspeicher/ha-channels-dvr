# Channels DVR for Home Assistant

A Home Assistant custom integration for the [Channels DVR](https://getchannels.com/dvr-server/)
server. It talks to the DVR's local API and exposes playback activity and
per-source maintenance actions as native Home Assistant entities.

## Entities

All entities are grouped under a single **Channels DVR** device per configured
server.

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.channels_dvr_active_streams` | Sensor | Number of streams currently playing. A `streams` attribute lists each one with its human-readable `description` (e.g. "Watching Saturday Night Live - Season 32, Episode 3 from TV at 0s"), `file_id`, and `client` address. |
| `binary_sensor.channels_dvr_playing` | Binary sensor (`running`) | On when at least one stream is active. Handy for simple automations ("pause the vacuum while someone is watching"). |
| `button.channels_dvr_refresh_<source>_m3u` | Button | One per M3U source; pressing it triggers a playlist re-fetch (`POST /providers/m3u/sources/<name>/refresh`). |

M3U sources are enumerated once at setup from `GET /dvr/lineups`. If you add or
remove a source on the DVR, reload the integration (Settings → Devices &
services → Channels DVR → Reload) to pick up the change.

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ → *Custom repositories*.
2. Add this repository's URL with category **Integration**.
3. Install **Channels DVR** and restart Home Assistant.

### Manual

Copy `custom_components/channels_dvr/` into your Home Assistant
`config/custom_components/` directory and restart Home Assistant.

## Configuration

Settings → Devices & services → *Add integration* → **Channels DVR**.

| Field | Default | Notes |
|-------|---------|-------|
| Host | — | Hostname or IP of the DVR server. |
| Port | `8089` | The DVR's API port. |
| Uses an SSL certificate | off | Enable if you reach the server over HTTPS (e.g. behind a reverse proxy). |
| Verify SSL certificate | on | Disable for self-signed or private-CA certificates. |

No token or credentials are needed — the Channels DVR API is unauthenticated on
the local network.

The integration polls `GET /dvr` every 15 seconds. When the server is
unreachable, all entities become unavailable until it responds again.

## Development

Dependencies are managed with [uv](https://docs.astral.sh/uv/):

```sh
uv sync                # install dev dependencies
uv run pytest          # run the test suite
uv run ruff check .    # lint
uv run ruff format .   # format
```

hassfest validation (requires a home-assistant/core checkout):

```sh
cd ~/Code/home-assistant/core
PATH="$PWD/../../rspeicher/ha-channels-dvr/.venv/bin:$PATH" \
  python -m script.hassfest --action validate \
  --integration-path ~/Code/rspeicher/ha-channels-dvr/custom_components/channels_dvr
```

API notes for the Channels DVR server live in [`docs/channels-dvr.md`](docs/channels-dvr.md).
Note the warning there: never call `GET /dvr/files` — the response is ~85MB and
has crashed servers. The API client in this integration deliberately has no
method for it.

## Extending

The coordinator already fetches the full `GET /dvr` payload each cycle
(`ChannelsDVRData.dvr`), which includes `disk`, `stats`, and `busy` — future
entities (disk usage, recording status, etc.) can read from it without new API
calls. Add new platforms by appending to `PLATFORMS` in
`custom_components/channels_dvr/__init__.py`.
