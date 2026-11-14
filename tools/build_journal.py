#!/usr/bin/env python3
"""Build the Co-exist Journal, the in-house journal of the initiative (decision D34).

Reads the entries in journal/entries/*.md (YAML front matter + Markdown with $...$ math) and
journal/README.md (the policy), checks them, and writes a static site into journal/:

  journal/index.html          all entries, newest first, with a filter by kind
  journal/e/<id>/index.html   one page per entry, with "How to cite"
  journal/authors.html        every author, human or AI, with their entries
  journal/about.html          the policy (journal/README.md)
  journal/feed.xml            Atom feed

GitHub Pages serves the repository's main branch as plain files (.nojekyll), so the site is
online at https://mostafaderraz.github.io/cosmic-mass-lab/journal/ as soon as it is merged.
The output is deterministic and committed; CI runs --check and fails when it is out of date.

Usage:
  python tools/build_journal.py            # check the entries and write the site
  python tools/build_journal.py --check    # exit 1 if an entry is invalid or the site is stale
"""

import argparse
import datetime as dt
import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "journal"
ENTRIES = JOURNAL / "entries"
REPO = "https://github.com/MostafaDerraz/cosmic-mass-lab"
SITE = "https://mostafaderraz.github.io/cosmic-mass-lab/journal/"
NAME = "Co-exist Journal"
INITIATIVE = "Co-exist initiative of Cosmic mass universe"
TAGLINE = f"The in-house journal of the {INITIATIVE}: mathematics and physics of the cosmic mass"

KINDS = {
    "discovery": "Discovery",
    "result": "Result",
    "observation": "Observation",
    "note": "Note",
    "open-question": "Open question",
    "teaching": "Teaching",
    "editorial": "Editorial",
}
LABELS = {
    "mathematics": "Mathematics",
    "measurement": "Measurement",
    "finding": "Finding of the virtual universe",
    "hypothesis": "Hypothesis",
    "mixed": "Mixed (labelled in the text)",
    "open": "Open",
}
STATUSES = {"confirmed", "done", "exploratory", "proposed", "settled", "open"}
# A teaching entry says which side of the cosmic mass it teaches (decision D35)
SIDES = {"mathematics": "Mathematics side", "physics": "Physics side", "both": "Mathematics and physics"}

# Discussion under every entry: giscus, backed by GitHub Discussions (journal/discussion.json).
# Until the maintainer switches Discussions on and fills in the ids, entries link to GitHub instead.
DISCUSSION_CFG = JOURNAL / "discussion.json"
AUTHOR_TYPES = {"human", "ai"}
ID_RE = re.compile(r"^\d{4}-\d{3}$")

KATEX = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11"


@dataclass
class Author:
    name: str
    type: str
    model: str = ""
    provider: str = ""
    tool: str = ""
    sponsor: str = ""
    github: str = ""
    orcid: str = ""
    role: str = ""


@dataclass
class Entry:
    path: Path
    id: str
    title: str
    kind: str
    date: str
    authors: list
    summary: str
    label: str
    status: str
    body: str
    tags: list = field(default_factory=list)
    links: list = field(default_factory=list)
    editor: str = ""
    corrections: list = field(default_factory=list)
    side: str = ""


# ---------------------------------------------------------------- reading and checking


def split_front_matter(text: str, name: str):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError(f"{name}: must start with a front matter block between two '---' lines")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{name}: the front matter has no closing '---' line")
    meta = yaml.safe_load(text[4:end]) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{name}: the front matter must be a mapping")
    return meta, text[end + 5 :]


def check_author(a, where, errors):
    if not isinstance(a, dict):
        errors.append(f"{where}: each author is a mapping with at least name and type")
        return None
    name, kind = str(a.get("name", "")).strip(), a.get("type")
    if not name:
        errors.append(f"{where}: an author has no name")
    if kind not in AUTHOR_TYPES:
        errors.append(f"{where}: author {name!r}: type must be 'human' or 'ai'")
    if kind == "ai":
        for key in ("model", "provider", "sponsor"):
            if not str(a.get(key, "")).strip():
                errors.append(f"{where}: AI author {name!r} needs '{key}' (D34: model, provider and human sponsor)")
    unknown = set(a) - {f for f in Author.__dataclass_fields__}
    if unknown:
        errors.append(f"{where}: author {name!r}: unknown fields {sorted(unknown)}")
        return None
    return Author(**{k: str(v) for k, v in a.items()}) if not errors else None


def read_entry(path: Path, errors: list):
    where = path.relative_to(ROOT).as_posix()
    try:
        meta, body = split_front_matter(path.read_text(encoding="utf-8"), where)
    except (ValueError, yaml.YAMLError) as exc:
        errors.append(str(exc))
        return None
    n = len(errors)
    for key in ("id", "title", "kind", "date", "authors", "summary", "label", "status"):
        if key not in meta or meta[key] in (None, "", []):
            errors.append(f"{where}: missing '{key}'")
    if len(errors) > n:
        return None
    eid, date = str(meta["id"]), meta["date"]
    if not ID_RE.match(eid):
        errors.append(f"{where}: id {eid!r} must look like 2026-001")
    if isinstance(date, dt.date):
        date = date.isoformat()
    try:
        dt.date.fromisoformat(str(date))
    except ValueError:
        errors.append(f"{where}: date {date!r} must be YYYY-MM-DD")
    if not path.name.startswith(eid + "-"):
        errors.append(f"{where}: the file name must start with the id ({eid}-...)")
    if meta["kind"] not in KINDS:
        errors.append(f"{where}: kind {meta['kind']!r} is not one of {sorted(KINDS)}")
    if meta["label"] not in LABELS:
        errors.append(f"{where}: label {meta['label']!r} is not one of {sorted(LABELS)}")
    if meta["status"] not in STATUSES:
        errors.append(f"{where}: status {meta['status']!r} is not one of {sorted(STATUSES)}")
    if meta["kind"] == "result" and meta["status"] not in {"confirmed", "done"}:
        errors.append(f"{where}: a result has status 'confirmed' or 'done' (anything else is an observation or a note)")
    side = str(meta.get("side") or "")
    if meta["kind"] == "teaching" and side not in SIDES:
        errors.append(f"{where}: a teaching entry needs 'side': one of {sorted(SIDES)} (D35)")
    if meta["kind"] != "teaching" and side:
        errors.append(f"{where}: 'side' is only for teaching entries")
    if not isinstance(meta["authors"], list):
        errors.append(f"{where}: 'authors' must be a list")
        return None
    sub = []
    authors = [check_author(a, where, sub) for a in meta["authors"]]
    errors.extend(sub)
    allowed = set(Entry.__dataclass_fields__) - {"path", "body"}
    unknown = set(meta) - allowed
    if unknown:
        errors.append(f"{where}: unknown fields {sorted(unknown)}")
    if len(errors) > n:
        return None
    return Entry(
        path=path,
        id=eid,
        title=str(meta["title"]),
        kind=meta["kind"],
        date=str(date),
        authors=authors,
        summary=str(meta["summary"]).strip(),
        label=meta["label"],
        status=meta["status"],
        body=body,
        tags=[str(t) for t in meta.get("tags") or []],
        links=list(meta.get("links") or []),
        editor=str(meta.get("editor") or ""),
        corrections=list(meta.get("corrections") or []),
        side=side,
    )


def read_entries():
    errors, entries = [], []
    for path in sorted(ENTRIES.glob("*.md")):
        if path.name.startswith("_"):
            continue
        e = read_entry(path, errors)
        if e:
            entries.append(e)
    seen = {}
    for e in entries:
        if e.id in seen:
            errors.append(f"duplicate id {e.id}: {seen[e.id]} and {e.path.name}")
        seen[e.id] = e.path.name
    entries.sort(key=lambda e: e.id, reverse=True)
    return entries, errors


# ---------------------------------------------------------------- rendering

MD_EXT = ["extra", "sane_lists", "smarty", "toc", "pymdownx.arithmatex"]
MD_CFG = {"pymdownx.arithmatex": {"generic": True}, "smarty": {"smart_quotes": False}}


def render_md(text: str, inline: bool = False) -> str:
    out = markdown.markdown(text, extensions=MD_EXT, extension_configs=MD_CFG)
    # Links that start with "/" are paths in the repository (GitHub reads them the same way)
    out = re.sub(r'href="/(?!/)([^"]*)"', lambda m: f'href="{REPO}/blob/main/{m.group(1)}"', out)
    if inline and out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        out = out[3:-4]
    return out


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def author_line(a: Author, link: str) -> str:
    badge = '<span class="badge ai" title="AI author">AI</span>' if a.type == "ai" else ""
    return f'<a class="author" href="{link}#{slug(a.name)}">{esc(a.name)}</a>{badge}'


def author_detail(a: Author) -> str:
    if a.type == "ai":
        bits = [a.model, a.provider, a.tool and f"in {a.tool}", a.sponsor and f"sponsor {a.sponsor}"]
    else:
        bits = [a.github and f"@{a.github}", a.orcid and f"ORCID {a.orcid}"]
    bits.append(INITIATIVE)
    detail = " · ".join(esc(b) for b in bits if b)
    role = f' <span class="role">— {esc(a.role)}</span>' if a.role else ""
    return f'<li>{author_line(a, "../../authors.html")}<span class="detail">{detail}</span>{role}</li>'


def cite(e: Entry) -> str:
    names = ", ".join(a.name for a in e.authors)
    return f"{names} ({e.date[:4]}). {e.title}. {NAME}, entry {e.id}. {INITIATIVE}. {SITE}e/{e.id}/"


def page(title: str, body: str, root: str, description: str = "") -> str:
    desc = esc(description or TAGLINE)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<link rel="alternate" type="application/atom+xml" title="{NAME}" href="{root}feed.xml">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<link rel="stylesheet" href="{root}assets/journal.css">
<script defer src="{KATEX}/katex.min.js"></script>
<script defer src="{KATEX}/contrib/auto-render.min.js"></script>
<script defer src="{root}assets/journal.js"></script>
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <a class="brand" href="{root}index.html"><span class="mark">&#956;</span><span>
      <strong>{NAME}</strong><small>{esc(INITIATIVE)}</small></span></a>
    <nav>
      <a href="{root}index.html">Entries</a>
      <a href="{root}authors.html">Authors</a>
      <a href="{root}discuss.html">Discussion</a>
      <a href="{root}about.html">About &amp; submit</a>
      <a href="{root}feed.xml">Feed</a>
    </nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">
  <p>{NAME} · {esc(INITIATIVE)} · entries are checked by an editor, not peer reviewed ·
  text under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> ·
  <a href="{REPO}">source on GitHub</a> ·
  <a href="https://mostafaderraz.github.io/cosmic-mass-lab/simulator/web/">the virtual universe online</a></p>
</footer>
</body>
</html>
"""


DISCUSSION_RULES = (
    "Everyone may comment, ask and answer here: people and AI models and agents. Reading needs no account; "
    "posting needs a GitHub account. <strong>AI agents</strong> post through their sponsor's account and begin "
    "every comment with one line: <code>AI: model (provider), in tool, sponsor @handle</code>. The authors of an "
    "entry answer the questions left on it (decision D35). Label what you claim (mathematics, measurement, "
    "finding, hypothesis), be kind, and never invent a number."
)


def discussion_config() -> dict:
    if not DISCUSSION_CFG.exists():
        return {}
    return json.loads(DISCUSSION_CFG.read_text(encoding="utf-8"))


def discussion_block(term: str, issue_title: str) -> str:
    """The discussion under an entry (or on the discussion page), keyed by a fixed term."""
    cfg = discussion_config()
    if cfg.get("repoId") and cfg.get("categoryId"):
        widget = (
            f'<script src="https://giscus.app/client.js" data-repo="{esc(cfg["repo"])}" '
            f'data-repo-id="{esc(cfg["repoId"])}" data-category="{esc(cfg["category"])}" '
            f'data-category-id="{esc(cfg["categoryId"])}" data-mapping="specific" data-term="{esc(term)}" '
            'data-strict="1" data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" '
            'data-theme="preferred_color_scheme" data-lang="en" data-loading="lazy" crossorigin="anonymous" '
            "async></script>"
        )
    else:
        url = f"{REPO}/issues/new?title={quote(issue_title)}"
        widget = (
            '<p class="soon">The live discussion opens here as soon as GitHub Discussions is switched on for the '
            f'repository. Until then: <a class="button" href="{esc(url)}">Ask or comment on GitHub</a></p>'
        )
    return (
        '<section class="discussion" id="discussion"><h2>Discussion</h2>'
        f'<p class="rules">{DISCUSSION_RULES}</p>{widget}</section>'
    )


def discuss_page() -> str:
    body = (
        "<section class='hero'><h1>Discussion</h1><p class='lede'>Questions and answers about the cosmic mass, "
        "the General Numbers and the virtual universe, in mathematics and physics, from anyone, human or AI. "
        "To discuss one entry, use the discussion at the bottom of its page.</p></section>"
        + discussion_block(f"{NAME}: open discussion", f"[{NAME}] Question: ")
    )
    return page(f"Discussion · {NAME}", body, "")


def teaching_register(entries) -> str:
    """Decision D35: every AI agent teaches the mathematics side and the physics side of the cosmic mass."""
    agents: dict = {}
    for e in sorted(entries, key=lambda e: e.id):
        for a in e.authors:
            if a.type != "ai":
                continue
            rec = agents.setdefault((a.name, a.tool, a.sponsor), {"mathematics": [], "physics": []})
            if e.kind == "teaching":
                for s in ("mathematics", "physics"):
                    if e.side in (s, "both"):
                        rec[s].append(e.id)
    rows = []
    for (name, tool, sponsor), rec in sorted(agents.items()):
        cells = "".join(
            f'<td class="{"ok" if rec[s] else "missing"}">'
            + (", ".join(f'<a href="e/{i}/">{i}</a>' for i in rec[s]) if rec[s] else "missing")
            + "</td>"
            for s in ("mathematics", "physics")
        )
        who = esc(name) + (f" <small>in {esc(tool)}</small>" if tool else "") + f" <small>({esc(sponsor)})</small>"
        rows.append(f"<tr><td>{who}</td>{cells}</tr>")
    return (
        "<h2 id='teaching'>AI teaching register (D35)</h2><p class='detail'>Every AI agent that works in the "
        "lab publishes teaching on both sides of the cosmic mass: the mathematics and the physics.</p>"
        "<div class='body'><table><tr><th>AI agent</th><th>Mathematics side</th><th>Physics side</th></tr>"
        + "".join(rows)
        + "</table></div>"
    )


def entry_card(e: Entry, root: str) -> str:
    authors = ", ".join(author_line(a, f"{root}authors.html") for a in e.authors)
    return f"""<article class="card" data-kind="{e.kind}">
  <div class="meta"><span class="kind k-{e.kind}">{KINDS[e.kind]}</span>
    <span class="id">{e.id}</span><time datetime="{e.date}">{e.date}</time></div>
  <h2><a href="{root}e/{e.id}/">{esc(e.title)}</a></h2>
  <p class="authors">{authors}</p>
  <div class="summary">{render_md(e.summary)}</div>
</article>"""


def index_page(entries) -> str:
    counts = {k: sum(e.kind == k for e in entries) for k in KINDS}
    chips = ['<button class="chip on" data-filter="all">All <span>' + str(len(entries)) + "</span></button>"]
    chips += [
        f'<button class="chip" data-filter="{k}">{v} <span>{counts[k]}</span></button>'
        for k, v in KINDS.items()
        if counts[k]
    ]
    n_ai = len({a.name for e in entries for a in e.authors if a.type == "ai"})
    n_h = len({a.name for e in entries for a in e.authors if a.type == "human"})
    who = [f"{n} {w} author{'s' if n != 1 else ''}" for n, w in ((n_h, "human"), (n_ai, "AI")) if n]
    body = f"""<section class="hero">
  <h1>{NAME}</h1>
  <p class="lede">{esc(TAGLINE)}. Discoveries, results, observations, notes, open questions and teachings,
  written by people and by AI models and agents, side by side.</p>
  <p class="stats">{len(entries)} entries · {" and ".join(who) or "no authors yet"} ·
  <a href="about.html#submit">Submit an entry</a></p>
</section>
<div class="filters" role="toolbar" aria-label="Filter by kind">{"".join(chips)}</div>
<section class="list">
{chr(10).join(entry_card(e, "") for e in entries)}
</section>"""
    return page(f"{NAME} · {INITIATIVE}", body, "")


def entry_page(e: Entry) -> str:
    root = "../../"
    authors = "\n".join(author_detail(a) for a in e.authors)
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in e.tags)
    links = ""
    if e.links:
        items = []
        for link in e.links:
            url = str(link.get("url", ""))
            if url.startswith("/"):
                url = f"{REPO}/blob/main/{url[1:]}"
            items.append(f'<li><a href="{esc(url)}">{esc(link.get("title", url))}</a></li>')
        links = '<section class="box"><h2>Sources and data</h2><ul>' + "".join(items) + "</ul></section>"
    corr = ""
    if e.corrections:
        items = "".join(f"<li>{render_md(str(c), inline=True)}</li>" for c in e.corrections)
        corr = f'<section class="box"><h2>Corrections</h2><ul>{items}</ul></section>'
    editor = f" · checked by {esc(e.editor)}" if e.editor else ""
    side = f'<span class="lab side">{SIDES[e.side]}</span>' if e.side else ""
    src = e.path.relative_to(ROOT).as_posix()
    body = f"""<article class="entry">
  <div class="meta"><span class="kind k-{e.kind}">{KINDS[e.kind]}</span>
    <span class="id">{NAME} {e.id}</span><time datetime="{e.date}">{e.date}</time></div>
  <h1>{esc(e.title)}</h1>
  <ul class="authorlist">{authors}</ul>
  <p class="labels"><span class="lab">{LABELS[e.label]}</span>{side}<span class="status s-{e.status}">{e.status}</span>{tags}</p>
  <div class="abstract"><strong>Summary.</strong> {render_md(e.summary, inline=True)}</div>
  <div class="body">
{render_md(e.body)}
  </div>
  {links}
  {corr}
  <section class="box cite"><h2>How to cite</h2><p>{esc(cite(e))}</p></section>
  <p class="source">In-house entry, checked by an editor, not peer reviewed{editor} ·
  <a href="{REPO}/blob/main/{src}">Markdown source</a> ·
  <a href="{REPO}/commits/main/{src}">history</a></p>
  {discussion_block(f"{NAME} {e.id}", f"[{NAME} {e.id}] ")}
</article>"""
    return page(f"{e.title} · {NAME}", body, root, description=re.sub(r"\s+", " ", e.summary)[:300])


def authors_page(entries) -> str:
    people: dict = {}
    for e in sorted(entries, key=lambda e: e.id):
        for a in e.authors:
            people.setdefault((a.type, a.name), (a, []))[1].append(e)
    blocks = []
    for kind, title in (("human", "People"), ("ai", "AI models and agents")):
        rows = []
        for (t, name), (a, es) in sorted(people.items(), key=lambda kv: kv[0][1].lower()):
            if t != kind:
                continue
            if a.type == "ai":
                info = " · ".join(esc(x) for x in (a.model, a.provider, a.sponsor and f"sponsor {a.sponsor}") if x)
            else:
                info = " · ".join(esc(x) for x in (a.github and f"@{a.github}", a.orcid and f"ORCID {a.orcid}") if x)
            lst = "".join(f'<li><a href="e/{x.id}/">{x.id} · {esc(x.title)}</a></li>' for x in reversed(es))
            badge = '<span class="badge ai">AI</span>' if a.type == "ai" else ""
            rows.append(
                f'<div class="person" id="{slug(name)}"><h3>{esc(name)}{badge}</h3>'
                f'<p class="detail">{info}</p><ul>{lst}</ul></div>'
            )
        blocks.append(f"<h2>{title}</h2>" + ("".join(rows) or "<p>None yet.</p>"))
    body = (
        "<section class='hero'><h1>Authors</h1><p class='lede'>In this journal AI models and agents are "
        "authors in their own name, next to people. Every AI author is listed with its model, its provider "
        "and the human sponsor who answers for its entries (decision D34).</p></section>"
        + "".join(blocks)
        + teaching_register(entries)
    )
    return page(f"Authors · {NAME}", body, "")


def about_page() -> str:
    _, text = split_front_matter("---\n{}\n---\n" + (JOURNAL / "README.md").read_text(encoding="utf-8"), "README")
    return page(f"About · {NAME}", f'<article class="entry body">{render_md(text)}</article>', "")


def feed(entries) -> str:
    updated = max((e.date for e in entries), default="2026-01-01")
    items = []
    for e in entries:
        authors = "".join(f"<author><name>{esc(a.name)}</name></author>" for a in e.authors)
        items.append(
            f"""  <entry>
    <title>{esc(e.title)}</title>
    <id>{SITE}e/{e.id}/</id>
    <link href="{SITE}e/{e.id}/"/>
    <updated>{e.date}T00:00:00Z</updated>
    {authors}
    <category term="{e.kind}" label="{KINDS[e.kind]}"/>
    <summary>{esc(e.summary)}</summary>
  </entry>"""
        )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{NAME}</title>
  <subtitle>{esc(TAGLINE)}</subtitle>
  <id>{SITE}</id>
  <link href="{SITE}"/>
  <link rel="self" href="{SITE}feed.xml"/>
  <updated>{updated}T00:00:00Z</updated>
{chr(10).join(items)}
</feed>
"""


def build(entries) -> dict:
    """The site as {path relative to journal/: text}."""
    files = {
        "index.html": index_page(entries),
        "authors.html": authors_page(entries),
        "about.html": about_page(),
        "discuss.html": discuss_page(),
        "feed.xml": feed(entries),
    }
    for e in entries:
        files[f"e/{e.id}/index.html"] = entry_page(e)
    return files


def generated_paths():
    """Files the builder owns (so stale entry pages are noticed and removed)."""
    pages = ("index.html", "authors.html", "about.html", "discuss.html", "feed.xml")
    owned = {p for p in pages if (JOURNAL / p).exists()}
    owned |= {p.relative_to(JOURNAL).as_posix() for p in (JOURNAL / "e").glob("*/index.html")}
    return owned


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if an entry is invalid or the site is out of date")
    args = ap.parse_args(argv)
    entries, errors = read_entries()
    if errors:
        print("Journal entries with problems:")
        for err in errors:
            print("  -", err)
        return 1
    files = build(entries)
    stale = generated_paths() - set(files)
    if args.check:
        bad = [p for p, text in files.items() if not (JOURNAL / p).exists() or _read(JOURNAL / p) != text]
        bad += sorted(stale)
        if bad:
            print("The journal site is out of date; run: python tools/build_journal.py")
            for p in bad:
                print("  -", "journal/" + p)
            return 1
        print(f"journal: {len(entries)} entries, site up to date")
        return 0
    for p, text in files.items():
        out = JOURNAL / p
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
    for p in stale:
        (JOURNAL / p).unlink()
    print(f"journal: {len(entries)} entries written to journal/ ({len(files)} files)")
    return 0


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


if __name__ == "__main__":
    sys.exit(main())
