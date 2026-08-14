"""Tests for activity parsing."""

from custom_components.channels_dvr.coordinator import StreamInfo, parse_activity


def test_parse_activity_idle() -> None:
    """An empty activity map means no streams."""
    assert parse_activity({}) == []


def test_parse_activity_single_stream() -> None:
    """A well-formed key yields file ID and client address."""
    activity = {
        "7B2A-file-9296-192.168.1.50": (
            "Watching Saturday Night Live - Season 32, Episode 3 from TV at 0s"
        )
    }
    assert parse_activity(activity) == [
        StreamInfo(
            session_key="7B2A-file-9296-192.168.1.50",
            description=(
                "Watching Saturday Night Live - Season 32, Episode 3 from TV at 0s"
            ),
            file_id=9296,
            client="192.168.1.50",
        )
    ]


def test_parse_activity_multiple_streams() -> None:
    """Concurrent streams each get an entry, sorted by key."""
    activity = {
        "b-file-2-10.0.0.2": "Watching B",
        "a-file-1-10.0.0.1": "Watching A",
    }
    streams = parse_activity(activity)
    assert [s.file_id for s in streams] == [1, 2]
    assert [s.description for s in streams] == ["Watching A", "Watching B"]


def test_parse_activity_dashed_session_prefix() -> None:
    """Session prefixes containing dashes still parse via the file- anchor."""
    activity = {"ab-cd-ef-file-42-fe80::1": "Watching X"}
    (stream,) = parse_activity(activity)
    assert stream.file_id == 42
    assert stream.client == "fe80::1"


def test_parse_activity_unrecognized_key_still_counts() -> None:
    """Keys without the file- marker still count as a stream."""
    activity = {"some-live-session": "Watching live TV"}
    (stream,) = parse_activity(activity)
    assert stream.file_id is None
    assert stream.client is None
    assert stream.description == "Watching live TV"
