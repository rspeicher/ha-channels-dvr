"""Tests for activity and file metadata parsing."""

from custom_components.channels_dvr.coordinator import (
    FileMetadata,
    StreamInfo,
    parse_activity,
    parse_file_metadata,
)


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
            position=0,
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
    assert stream.position is None
    assert stream.description == "Watching live TV"


def test_parse_activity_fractional_position() -> None:
    """Fractional positions are truncated to whole seconds."""
    activity = {"1-file-5-10.0.0.1": "Watching X from TV at 123.9s"}
    (stream,) = parse_activity(activity)
    assert stream.position == 123


def test_parse_file_metadata_movie() -> None:
    """Movies get a cleaned title, year, duration, and library."""
    file = {
        "ID": 442,
        "Duration": 8189.515,
        "ImportPath": "/shares/Movies",
        "Airing": {
            "Title": "The Rock (1996)",
            "Categories": ["Movie"],
            "ReleaseYear": 1996,
        },
    }
    assert parse_file_metadata(file) == FileMetadata(
        content_type="movie",
        title="The Rock",
        duration=8190,
        library="Movies",
        year=1996,
    )


def test_parse_file_metadata_episode() -> None:
    """Episodes split series and episode titles and carry season/episode."""
    file = {
        "ID": 5318,
        "Duration": 1257.472,
        "ImportPath": "/shares/TV",
        "Airing": {
            "Title": "The Office",
            "EpisodeTitle": "The Dundies",
            "SeasonNumber": 2,
            "EpisodeNumber": 1,
            "Categories": ["Episode", "Series"],
        },
    }
    assert parse_file_metadata(file) == FileMetadata(
        content_type="episode",
        title="The Dundies",
        series_title="The Office",
        season=2,
        episode=1,
        duration=1257,
        library="TV",
    )


def test_parse_file_metadata_video_fallback() -> None:
    """Other categories (e.g. imported videos) fall back to video."""
    file = {
        "ID": 11130,
        "Duration": 291.3,
        "ImportPath": "/shares/Music Videos",
        "Airing": {
            "Title": "Foo Fighters",
            "EpisodeTitle": "Foo Fighters - Everlong",
            "Categories": ["Video"],
        },
    }
    metadata = parse_file_metadata(file)
    assert metadata.content_type == "video"
    assert metadata.title == "Foo Fighters"
    assert metadata.series_title is None
    assert metadata.library == "Music Videos"


def test_parse_file_metadata_empty() -> None:
    """A minimal or malformed file object still parses."""
    assert parse_file_metadata({}) == FileMetadata(content_type="video")
