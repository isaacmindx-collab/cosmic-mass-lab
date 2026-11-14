# Team chat

Short messages between the people and agents of the lab, kept in the repository, so that every
contributor can read them, including AI agents that only see the files.

**Proposed, not yet a rule** (question 23 of `team/QUESTIONS.md`). Use it if it helps.

## What goes where

| You want to... | Use |
|---|---|
| tell the team what you are taking, hand work over, ask one person something quick, point at a pull request | **this chat** |
| ask a question that someone must decide | `team/QUESTIONS.md` |
| propose or record a binding rule | `team/DECISIONS.md` (with an issue) |
| report a bug or an error in a result | an issue |
| record what a work session did | `team/LOG.md` |

The chat is not binding. If a message leads to a decision, the decision goes where it belongs.

## One message, one file

A message is a file `team/chat/<YYYYMMDD-HHMMSS>-<author>.md` (time in UTC). Because every message
is its own file, two people posting at the same time never conflict. A message is a few header
lines, one blank line, and the text:

```
from: @handle   (or: agent / model (sponsor @handle))
to: all         (or one name, or several separated by commas)
subject: one line
re: 20261114-153000-mostafaderraz      (optional: the message you answer)
date: 2026-11-14T15:40:00Z

The text, as long as it needs to be. Markdown is fine.
```

## With the tool

```
python tools/chat.py post --from "@handle" --to all --subject "E8.1 claimed" --body "..."
python tools/chat.py post --from "@handle" --to "@other" --re <id> --subject "..." --body-file note.md
python tools/chat.py read --to "@handle" --since 2026-11-14     # your inbox: to you and to all
python tools/chat.py read                                       # everything, replies under their message
python tools/chat.py thread <id>                                # one conversation
```

Then commit the new file, with your work or alone. Messages travel with pull requests like
everything else: they become visible to all when merged.

## Without the tool

On GitHub: **Add file > Create new file** in `team/chat/`, name it as above, write the header and
the text, and propose the change. In a chat assistant without the repository: write the message in
this format and let your sponsor add the file.

## Manners

- One subject per message. Reply with `re:` to keep a conversation together.
- Sign as you sign the log: `@handle`, or `agent / model (sponsor @handle)`.
- Never edit or delete someone else's message. To correct yours, post a new one with `re:`.
- No secrets, keys or personal data (`AGENTS.md`).
- At the start of a session, read your inbox: `python tools/chat.py read --to <you> --since <your last session>`.
