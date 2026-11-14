"""The team chat: short messages between contributors, kept in the repository (`team/chat/`).

One message is one file, `team/chat/<YYYYMMDD-HHMMSS>-<author>.md`, so two people posting at
the same time never conflict. A message is a few header lines, a blank line, and the text:

    from: Claude Opus 5.5 in OpenCode (sponsor @MostafaDerraz)
    to: all
    subject: E8.1 claimed
    re: 20261114-153000-mostafaderraz          (optional: the message this answers)
    date: 2026-11-14T15:40:00Z

    I take E8.1 (pressure and temperature on walls) ...

Use it for coordination: who is on what, handoffs, quick questions to one person, "please look
at #35". It is not binding. Decisions go to `team/DECISIONS.md`, open questions that someone
must decide to `team/QUESTIONS.md`, bugs to issues, the record of a session to `team/LOG.md`.

    python tools/chat.py post --from "@handle" --to all --subject "..." --body "..."
    python tools/chat.py post --from "@handle" --to "@other" --re <id> --subject "..." --body-file note.md
    python tools/chat.py read                          # every message, oldest first, replies under their message
    python tools/chat.py read --to "@handle" --since 2026-11-14     # your inbox (messages to you and to all)
    python tools/chat.py thread <id>                   # one message and every reply to it
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAT = ROOT / "team" / "chat"
FIELDS = ("from", "to", "subject", "re", "date")
REQUIRED = ("from", "to", "subject", "date")

__all__ = ["Message", "ChatError", "post", "load", "inbox", "thread", "render", "main"]


class ChatError(ValueError):
    """A message cannot be written or read; the text says why."""


@dataclass(frozen=True)
class Message:
    id: str  # the file name without ".md"
    sender: str
    to: str
    subject: str
    date: str  # ISO 8601, UTC
    body: str
    re: str = ""

    def addressed_to(self, name: str) -> bool:
        """True for messages to `all`, or whose `to` names `name` (case-insensitive; several names may be
        given, separated by commas)."""
        wanted = name.strip().lower().lstrip("@")
        names = [n.strip().lower().lstrip("@") for n in self.to.split(",")]
        return "all" in names or any(wanted and wanted in n for n in names)


def _slug(text: str) -> str:
    """The author part of a file name: the signature without its "(sponsor ...)", in a-z0-9 and dashes."""
    slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"\(.*?\)", "", text).lower()).strip("-")
    return slug[:40].rstrip("-") or "anonymous"


def post(
    sender: str, to: str, subject: str, body: str, re_id: str = "", folder: Path = CHAT, now: datetime | None = None
) -> Path:
    """Write one message; return its file. Nothing is written if a field is missing."""
    fields = {"from": sender, "to": to, "subject": subject}
    for name, value in fields.items():
        if not value or not value.strip() or "\n" in value:
            raise ChatError(f"'{name}' must be one non-empty line")
    if not body.strip():
        raise ChatError("the message has no text")
    folder = Path(folder)
    if re_id and not (folder / f"{re_id}.md").exists():
        raise ChatError(f"'re': no message {re_id!r} in {folder}")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stem = f"{now:%Y%m%d-%H%M%S}-{_slug(sender)}"
    path, n = folder / f"{stem}.md", 2
    while path.exists():  # the same author twice in one second
        path, n = folder / f"{stem}-{n}.md", n + 1
    header = [f"from: {sender.strip()}", f"to: {to.strip()}", f"subject: {subject.strip()}"]
    if re_id:
        header.append(f"re: {re_id}")
    header.append(f"date: {now:%Y-%m-%dT%H:%M:%SZ}")
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header) + "\n\n" + body.strip() + "\n", encoding="utf-8")
    return path


def _parse(path: Path) -> Message:
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    head, _, body = text.replace("\r\n", "\n").partition("\n\n")
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if not sep or key not in FIELDS:
            raise ChatError(f"{path.name}: the header line {line!r} is not one of {', '.join(FIELDS)}")
        fields[key] = value.strip()
    missing = [k for k in REQUIRED if not fields.get(k)]
    if missing:
        raise ChatError(f"{path.name}: missing {', '.join(missing)}")
    return Message(
        id=path.stem,
        sender=fields["from"],
        to=fields["to"],
        subject=fields["subject"],
        date=fields["date"],
        body=body.strip(),
        re=fields.get("re", ""),
    )


def load(folder: Path = CHAT) -> list[Message]:
    """Every message, oldest first (the file names sort by time). `README.md` is not a message."""
    folder = Path(folder)
    if not folder.exists():
        return []
    return [_parse(p) for p in sorted(folder.glob("*.md")) if p.name.lower() != "readme.md"]


def inbox(messages: list[Message], name: str = "", since: str = "") -> list[Message]:
    """Messages to `name` (and to all), on or after the date `since` (YYYY-MM-DD)."""
    out = [m for m in messages if not name or m.addressed_to(name)]
    return [m for m in out if not since or m.date[:10] >= since]


def thread(messages: list[Message], root_id: str) -> list[Message]:
    """The message `root_id` and every reply to it, at any depth, oldest first."""
    ids, out = {root_id}, []
    for m in messages:  # oldest first: a reply always comes after what it answers
        if m.id in ids or m.re in ids:
            ids.add(m.id)
            out.append(m)
    if not out or out[0].id != root_id:
        raise ChatError(f"no message {root_id!r}")
    return out


def render(messages: list[Message]) -> str:
    """Messages as text, replies indented under the message they answer when it is shown."""
    shown = {m.id for m in messages}
    depth = {}
    lines = []
    for m in messages:
        depth[m.id] = depth.get(m.re, -1) + 1 if m.re in shown else 0
        pad = "    " * depth[m.id]
        lines.append(f"{pad}[{m.id}] {m.date}  {m.sender} -> {m.to}")
        lines.append(f"{pad}  {m.subject}" + (f"  (re {m.re})" if m.re and m.re not in shown else ""))
        lines.extend(f"{pad}  | {line}" for line in m.body.splitlines())
        lines.append("")
    return "\n".join(lines) if lines else "no messages"


def main(argv=None, folder: Path = CHAT) -> int:
    parser = argparse.ArgumentParser(prog="python tools/chat.py", description="The team chat (team/chat/).")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("post", help="write a message")
    p.add_argument("--from", dest="sender", required=True, help='"@handle" or "agent / model (sponsor @handle)"')
    p.add_argument("--to", required=True, help='"all", or names separated by commas')
    p.add_argument("--subject", required=True)
    p.add_argument("--re", default="", help="the id of the message this answers")
    text = p.add_mutually_exclusive_group(required=True)
    text.add_argument("--body")
    text.add_argument("--body-file")
    r = commands.add_parser("read", help="read messages, oldest first")
    r.add_argument("--to", default="", help="only messages to this name (and to all)")
    r.add_argument("--since", default="", help="only messages on or after YYYY-MM-DD")
    t = commands.add_parser("thread", help="one message and its replies")
    t.add_argument("id")
    args = parser.parse_args(argv)
    try:
        if args.command == "post":
            body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")
            path = post(args.sender, args.to, args.subject, body, args.re, folder)
            print(f"posted {path.stem} ({path.relative_to(folder.parent.parent) if folder == CHAT else path})")
            print("commit the file with your work, or alone, so the others see it")
        elif args.command == "read":
            print(render(inbox(load(folder), args.to, args.since)))
        else:
            print(render(thread(load(folder), args.id)))
    except (ChatError, OSError) as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
