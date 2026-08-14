"""Constants for the Channels DVR integration."""

from __future__ import annotations

from datetime import timedelta
import logging
import re
from typing import Final

DOMAIN: Final = "channels_dvr"
LOGGER = logging.getLogger(__package__)

DEFAULT_PORT: Final = 8089
SCAN_INTERVAL: Final = timedelta(seconds=15)

M3U_PREFIX: Final = "M3U-"

# Activity keys look like "{session}-file-{file_id}-{client}". The session
# prefix may itself contain dashes, so anchor on the "file-" marker and treat
# everything after the file ID as the client address.
ACTIVITY_KEY_RE: Final = re.compile(r"file-(\d+)-(.+)$")
