"""The team chat (`tools/chat.py`, `team/chat/`): one message per file, inbox, threads."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import chat  # noqa: E402

T0 = datetime(2026, 11, 14, 15, 0, 0, tzinfo=timezone.utc)


def test_post_writes_one_file_with_its_header(tmp_path):
    path = chat.post("@alice", "all", "Hello", "First line.\nSecond line.", folder=tmp_path, now=T0)
    assert path.name == "20261114-150000-alice.md"
    assert path.read_text(encoding="utf-8") == (
        "from: @alice\nto: all\nsubject: Hello\ndate: 2026-11-14T15:00:00Z\n\nFirst line.\nSecond line.\n"
    )
    (m,) = chat.load(tmp_path)
    assert (m.id, m.sender, m.to, m.subject, m.body) == (
        "20261114-150000-alice",
        "@alice",
        "all",
        "Hello",
        "First line.\nSecond line.",
    )


def test_two_messages_in_one_second_do_not_collide(tmp_path):
    a = chat.post("@alice", "all", "a", "x", folder=tmp_path, now=T0)
    b = chat.post("@alice", "all", "b", "y", folder=tmp_path, now=T0)
    assert a != b and b.name == "20261114-150000-alice-2.md"
    c = chat.post("Claude Opus 5.5 in OpenCode (sponsor @alice)", "all", "c", "z", folder=tmp_path, now=T0)
    assert c.name == "20261114-150000-claude-opus-5-5-in-opencode.md"  # the sponsor is not in the file name


def test_inbox_and_threads(tmp_path):
    root = chat.post("@alice", "all", "Who takes E8.1?", "?", folder=tmp_path, now=T0)
    reply = chat.post(
        "Claude Opus 5.5 (sponsor @alice)",
        "@alice",
        "Me",
        "I do.",
        re_id=root.stem,
        folder=tmp_path,
        now=T0 + timedelta(minutes=1),
    )
    chat.post("@bob", "@carol, @dave", "Private", "...", folder=tmp_path, now=T0 + timedelta(days=1))
    later = chat.post(
        "@alice",
        "claude opus 5.5",
        "Thanks",
        "ok",
        re_id=reply.stem,
        folder=tmp_path,
        now=T0 + timedelta(days=1, minutes=1),
    )
    messages = chat.load(tmp_path)
    assert [m.subject for m in chat.inbox(messages, "@alice")] == ["Who takes E8.1?", "Me"]
    assert [m.subject for m in chat.inbox(messages, "Claude Opus 5.5")] == ["Who takes E8.1?", "Thanks"]
    assert [m.subject for m in chat.inbox(messages, "dave")] == ["Who takes E8.1?", "Private"]
    assert [m.subject for m in chat.inbox(messages, since="2026-11-15")] == ["Private", "Thanks"]
    assert [m.id for m in chat.thread(messages, root.stem)] == [root.stem, reply.stem, later.stem]
    text = chat.render(chat.thread(messages, root.stem))
    assert "\n    [" in text and "\n        [" in text  # a reply is indented under its message, and so on


def test_bad_messages_are_refused_and_nothing_is_written(tmp_path):
    for sender, to, subject, body in (
        ("", "all", "s", "b"),
        ("@a", " ", "s", "b"),
        ("@a", "all", "two\nlines", "b"),
        ("@a", "all", "s", "  "),
    ):
        with pytest.raises(chat.ChatError):
            chat.post(sender, to, subject, body, folder=tmp_path, now=T0)
    with pytest.raises(chat.ChatError, match="no message"):
        chat.post("@a", "all", "s", "b", re_id="20990101-000000-nobody", folder=tmp_path, now=T0)
    assert list(tmp_path.iterdir()) == []


def test_messages_written_by_hand_are_read_and_checked(tmp_path):
    (tmp_path / "README.md").write_text("# not a message\n", encoding="utf-8")
    # a byte-order mark, Windows line ends and a capital in a key, as an editor might write it
    (tmp_path / "20261114-160000-bob.md").write_bytes(
        "\ufeffFrom: @bob\r\nto: all\r\nsubject: by hand\r\ndate: 2026-11-14T16:00:00Z\r\n\r\nWritten on GitHub.\r\n".encode(
            "utf-8"
        )
    )
    (m,) = chat.load(tmp_path)
    assert m.sender == "@bob" and m.body == "Written on GitHub."
    (tmp_path / "20261114-170000-eve.md").write_text("from: @eve\ncolour: red\n\nx\n", encoding="utf-8")
    with pytest.raises(chat.ChatError, match="not one of"):
        chat.load(tmp_path)
    (tmp_path / "20261114-170000-eve.md").write_text("from: @eve\nto: all\n\nx\n", encoding="utf-8")
    with pytest.raises(chat.ChatError, match="missing subject, date"):
        chat.load(tmp_path)


def test_the_command_line(tmp_path, capsys):
    assert chat.main(["post", "--from", "@alice", "--to", "all", "--subject", "Hi", "--body", "hello"], tmp_path) == 0
    (msg,) = chat.load(tmp_path)
    note = tmp_path.parent / "note.md"
    note.write_text("a longer answer\n", encoding="utf-8")
    assert (
        chat.main(
            [
                "post",
                "--from",
                "@bob",
                "--to",
                "@alice",
                "--re",
                msg.id,
                "--subject",
                "Re: Hi",
                "--body-file",
                str(note),
            ],
            tmp_path,
        )
        == 0
    )
    capsys.readouterr()
    assert chat.main(["read", "--to", "@alice"], tmp_path) == 0
    out = capsys.readouterr().out
    assert "Hi" in out and "| a longer answer" in out
    assert chat.main(["thread", msg.id], tmp_path) == 0 and "Re: Hi" in capsys.readouterr().out
    assert chat.main(["thread", "nope"], tmp_path) == 2 and "error" in capsys.readouterr().out
    assert chat.main(["read"], tmp_path / "empty") == 0 and "no messages" in capsys.readouterr().out


def test_the_messages_of_the_repository_are_well_formed():
    for message in chat.load():  # every committed message parses
        assert message.id[:15].replace("-", "").isdigit()
        assert message.addressed_to(message.to.split(",")[0])
