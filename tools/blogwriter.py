#!/usr/bin/env python3
"""blogwriter: a tiny local blog editor for this Hugo site. One file, stdlib only.

    python3 tools/blogwriter.py            # then it opens http://127.0.0.1:8765
    python3 tools/blogwriter.py --port 9000 --no-browser

What it does
  * lists posts in content/posts/*/index.md, creates new ones (slug, folder and
    front matter generated for you, author copied from your latest post)
  * markdown editor with live preview (renderer is built in, no CDN)
  * drag & drop or paste images: saved next to the post's index.md and linked
    with a relative path, which is how the existing posts do it
  * bare minimum vim: toggle in the header. Normal/insert, hjkl w b 0 $ gg G,
    i a I A o O x dd yy p P D u, counts, :w :wq
  * Ctrl-S saves. "Publish" runs git add/commit/push for that post only, after
    a confirm prompt.

Only listens on 127.0.0.1 and rejects requests whose Host/Origin isn't local.
"""
import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
MAX_UPLOAD = 25 * 1024 * 1024
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def find_repo(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "hugo.toml").exists() and (p / "content").is_dir():
            return p
    sys.exit("could not find hugo.toml; pass --repo /path/to/site")


class Blog:
    def __init__(self, repo: Path):
        self.repo = repo
        self.posts = repo / "content" / "posts"

    # ---- helpers -------------------------------------------------------
    def post_dir(self, slug: str) -> Path:
        if not SLUG_RE.match(slug or "") or slug.startswith("."):
            raise ValueError("bad slug")
        d = (self.posts / slug).resolve()
        if d.parent != self.posts.resolve():
            raise ValueError("bad slug")
        return d

    @staticmethod
    def front(text: str) -> dict:
        m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
        out = {}
        if m:
            for line in m.group(1).splitlines():
                k = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
                if k:
                    out[k.group(1)] = k.group(2).strip().strip("'\"")
        return out

    def list_posts(self):
        rows = []
        for f in self.posts.glob("*/index.md"):
            fm = self.front(f.read_text(errors="replace"))
            rows.append({
                "slug": f.parent.name,
                "title": fm.get("title", f.parent.name),
                "date": fm.get("date", ""),
                "inprogress": fm.get("inprogress", "") == "true",
                "draft": fm.get("draft", "") == "true",
            })
        rows.sort(key=lambda r: r["date"], reverse=True)
        return rows

    def default_author(self) -> str:
        for r in self.list_posts():
            a = self.front((self.posts / r["slug"] / "index.md").read_text(errors="replace")).get("author")
            if a:
                return a
        try:
            return subprocess.run(["git", "config", "user.name"], cwd=self.repo,
                                  capture_output=True, text=True).stdout.strip() or "Author"
        except OSError:
            return "Author"

    def new_post(self, title, slug, description, tags):
        title = (title or "").strip()
        if not title:
            raise ValueError("title required")
        slug = slug or slugify(title)
        d = self.post_dir(slug)
        if d.exists():
            raise FileExistsError(slug)
        d.mkdir(parents=True)
        tag_lines = "".join(f"  - {t}\n" for t in tags) if tags else ""
        body = (
            "---\n"
            f"title: {yaml_str(title)}\n"
            f"date: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"author: {self.default_author()}\n"
            f"description: {yaml_str(description or '')}\n"
            + (f"tags:\n{tag_lines}" if tags else "")
            + "toc: false\n"
            "---\n\n"
        )
        (d / "index.md").write_text(body)
        return slug

    def save_image(self, slug, name, data):
        d = self.post_dir(slug)
        if not d.is_dir():
            raise FileNotFoundError(slug)
        base, ext = os.path.splitext(os.path.basename(name or "image.png"))
        ext = ext.lower()
        if ext not in IMG_EXT:
            raise ValueError("not an image type")
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-.") or "image"
        final, n = f"{base}{ext}", 1
        while (d / final).exists():
            final, n = f"{base}-{n}{ext}", n + 1
        (d / final).write_bytes(data)
        return final

    def git(self, *args):
        p = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        return p.returncode, (p.stdout + p.stderr).strip()

    def publish(self, slug, message):
        d = self.post_dir(slug)
        rel = str(d.relative_to(self.repo))
        log = []
        for args in (["add", "--", rel],
                     ["commit", "-m", message or f"Add/update post {slug}", "--", rel],
                     ["push"]):
            code, out = self.git(*args)
            log.append(f"$ git {' '.join(args[:2])}\n{out}")
            if code != 0:
                return False, "\n\n".join(log)
        return True, "\n\n".join(log)


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "post"


def yaml_str(s):
    # quote only when YAML would choke
    if s == "" or re.search(r"[:#\[\]{}&*!|>'\"%@`]|^\s|\s$|^[-?]", s):
        return json.dumps(s)
    return s


class Handler(BaseHTTPRequestHandler):
    blog: Blog = None
    port = 0
    server_version = "blogwriter"

    def log_message(self, *a):
        pass

    # ---- plumbing ------------------------------------------------------
    def _local_ok(self):
        host = self.headers.get("Host", "")
        ok = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        if host not in ok:
            return False
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).netloc not in ok:
            return False
        return True

    def _send(self, code, body=b"", ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, {"error": msg})

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_UPLOAD:
            raise ValueError("too large")
        return self.rfile.read(n)

    # ---- routes --------------------------------------------------------
    def do_GET(self):
        if not self._local_ok():
            return self._err(403, "forbidden")
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if u.path == "/api/posts":
                return self._send(200, {"posts": self.blog.list_posts(),
                                        "repo": str(self.blog.repo)})
            if u.path == "/api/post":
                d = self.blog.post_dir(q.get("slug", ""))
                f = d / "index.md"
                if not f.exists():
                    return self._err(404, "no such post")
                files = sorted(p.name for p in d.iterdir() if p.is_file() and p.name != "index.md")
                return self._send(200, {"content": f.read_text(), "files": files})
            if u.path.startswith("/files/"):
                parts = unquote(u.path[len("/files/"):]).split("/")
                if len(parts) != 2:
                    return self._err(404, "not found")
                d = self.blog.post_dir(parts[0])
                f = (d / parts[1]).resolve()
                if f.parent != d or not f.is_file():
                    return self._err(404, "not found")
                ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                return self._send(200, f.read_bytes(), ctype)
            return self._err(404, "not found")
        except (ValueError, FileNotFoundError) as e:
            return self._err(400, str(e))

    def do_POST(self):
        if not self._local_ok():
            return self._err(403, "forbidden")
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/image":
                name = self.blog.save_image(q.get("slug", ""), q.get("name", ""), self._body())
                return self._send(200, {"name": name})
            data = json.loads(self._body() or b"{}")
            if u.path == "/api/post":
                d = self.blog.post_dir(data.get("slug", ""))
                if not (d / "index.md").exists():
                    return self._err(404, "no such post")
                tmp = d / ".index.md.tmp"
                tmp.write_text(data.get("content", ""))
                tmp.replace(d / "index.md")
                return self._send(200, {"ok": True})
            if u.path == "/api/new":
                tags = [t.strip() for t in re.split(r"[,\n]", data.get("tags", "")) if t.strip()]
                slug = self.blog.new_post(data.get("title"), (data.get("slug") or "").strip(),
                                          data.get("description"), tags)
                return self._send(200, {"slug": slug})
            if u.path == "/api/publish":
                ok, log = self.blog.publish(data.get("slug", ""), data.get("message", ""))
                return self._send(200 if ok else 500, {"ok": ok, "log": log})
            return self._err(404, "not found")
        except FileExistsError:
            return self._err(409, "a post with that slug already exists")
        except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
            return self._err(400, str(e))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, help="site root (default: auto-detect)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    repo = a.repo.resolve() if a.repo else find_repo(Path(__file__).resolve().parent)
    Handler.blog = Blog(repo)
    Handler.port = a.port
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"blogwriter on {url}  (repo: {repo})  ctrl-c to quit")
    if not a.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>blogwriter</title>
<style>
:root{--bg:#fafafa;--fg:#1c1c1e;--mut:#6b7280;--pane:#fff;--line:#e5e7eb;--acc:#2563eb;--code:#f3f4f6;--ok:#15803d;--bad:#b91c1c}
@media (prefers-color-scheme:dark){:root{--bg:#141416;--fg:#e5e7eb;--mut:#9ca3af;--pane:#1b1b1f;--line:#2a2a30;--acc:#60a5fa;--code:#26262b;--ok:#4ade80;--bad:#f87171}}
*{box-sizing:border-box}
html,body{height:100%;margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
button,input,select{font:inherit;color:inherit}
button{background:var(--pane);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
button:hover{border-color:var(--acc)}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff}
#app{display:grid;grid-template-columns:240px 1fr;height:100%}
#side{border-right:1px solid var(--line);background:var(--pane);display:flex;flex-direction:column;min-height:0}
#side header{padding:10px;border-bottom:1px solid var(--line);display:flex;gap:6px;align-items:center}
#side header b{flex:1}
#list{overflow:auto;flex:1}
.item{padding:8px 12px;border-bottom:1px solid var(--line);cursor:pointer}
.item:hover{background:var(--code)}.item.sel{border-left:3px solid var(--acc);padding-left:9px;background:var(--code)}
.item small{display:block;color:var(--mut)}
#main{display:flex;flex-direction:column;min-width:0;min-height:0}
#bar{display:flex;gap:8px;align-items:center;padding:8px 12px;border-bottom:1px solid var(--line);background:var(--pane)}
#bar .sp{flex:1}#bar label{color:var(--mut);display:flex;gap:4px;align-items:center}
#cur{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#state{color:var(--mut);font-size:13px}
#panes{flex:1;display:grid;grid-template-columns:1fr 1fr;min-height:0}
#edwrap{display:flex;flex-direction:column;min-height:0;border-right:1px solid var(--line);position:relative}
#ed{flex:1;width:100%;border:0;outline:0;resize:none;padding:14px;background:var(--pane);color:var(--fg);
  font:14px/1.55 ui-monospace,Menlo,Consolas,monospace;tab-size:4;white-space:pre-wrap}
#ed.normal{caret-color:transparent}
#ed.normal::selection{background:var(--acc);color:#fff}
#status{padding:3px 12px;font:12px ui-monospace,monospace;border-top:1px solid var(--line);background:var(--pane);color:var(--mut);display:flex;gap:12px}
#status .mode{font-weight:700;color:var(--acc)}
#drop{position:absolute;inset:0;background:color-mix(in srgb,var(--acc) 15%,transparent);border:2px dashed var(--acc);display:none;align-items:center;justify-content:center;font-size:18px;pointer-events:none}
#prev{overflow:auto;padding:18px 26px;background:var(--bg)}
#prev img{max-width:100%}
#prev pre{background:var(--code);padding:10px 12px;border-radius:6px;overflow:auto}
#prev code{background:var(--code);padding:1px 4px;border-radius:4px;font-size:.92em}
#prev pre code{padding:0;background:none}
#prev blockquote{margin:.8em 0;padding:.1em 1em;border-left:3px solid var(--line);color:var(--mut)}
#prev table{border-collapse:collapse}#prev td,#prev th{border:1px solid var(--line);padding:4px 10px}
#prev h1,#prev h2,#prev h3{line-height:1.25}#prev a{color:var(--acc)}
#prev .fm{color:var(--mut);font-size:13px;border-bottom:1px solid var(--line);margin-bottom:14px;padding-bottom:8px}
#empty{margin:auto;color:var(--mut)}
dialog{border:1px solid var(--line);border-radius:10px;background:var(--pane);color:var(--fg);min-width:340px}
dialog::backdrop{background:#0006}
dialog label{display:block;margin:8px 0 2px;color:var(--mut);font-size:13px}
dialog input{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg)}
dialog .row{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}
pre#log{max-width:70vw;max-height:50vh;overflow:auto;background:var(--code);padding:8px;border-radius:6px;white-space:pre-wrap}
@media (max-width:800px){#app{grid-template-columns:1fr}#side{display:none}#panes{grid-template-columns:1fr}#prev{display:none}}
</style></head>
<body>
<div id="app">
  <aside id="side">
    <header><b>posts</b><button id="newbtn" class="primary">+ new</button></header>
    <div id="list"></div>
  </aside>
  <section id="main">
    <div id="bar">
      <span id="cur">no post open</span><span id="state"></span><span class="sp"></span>
      <label><input type="checkbox" id="vimtoggle"> vim</label>
      <button id="savebtn">Save</button>
      <button id="pubbtn">Publish</button>
    </div>
    <div id="panes">
      <div id="edwrap">
        <textarea id="ed" spellcheck="false" disabled placeholder="open or create a post. Drop or paste images here."></textarea>
        <div id="drop">drop image to upload</div>
        <div id="status"><span class="mode" id="mode"></span><span id="msg"></span><span class="sp" style="flex:1"></span><span id="pos"></span></div>
      </div>
      <div id="prev"><div id="empty">preview</div></div>
    </div>
  </section>
</div>

<dialog id="newdlg"><form method="dialog" id="newform">
  <b>New post</b>
  <label>Title</label><input id="n_title" required autofocus>
  <label>Folder / slug</label><input id="n_slug" pattern="[A-Za-z0-9][A-Za-z0-9._-]*">
  <label>Description</label><input id="n_desc">
  <label>Tags (comma separated)</label><input id="n_tags">
  <div class="row"><button type="button" id="n_cancel">Cancel</button><button class="primary" id="n_ok">Create</button></div>
</form></dialog>

<dialog id="pubdlg"><form method="dialog">
  <b>Publish</b>
  <p style="color:var(--mut);margin:6px 0">Runs <code>git add</code>, <code>commit</code> and <code>push</code> for this post's folder only. Saves first.</p>
  <label>Commit message</label><input id="p_msg">
  <pre id="log" hidden></pre>
  <div class="row"><button type="button" id="p_cancel">Close</button><button class="primary" id="p_ok">Commit &amp; push</button></div>
</form></dialog>

<script>
"use strict";
const $ = id => document.getElementById(id);
const ed = $("ed"), prev = $("prev");
let slug = null, dirty = false, files = [], snaps = [], reg = "", regLine = false;

// ---------- api ----------
async function api(path, body, raw) {
  const opt = body === undefined ? {} : raw
    ? {method: "POST", body: body}
    : {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)};
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
function setState(t) { $("state").textContent = t; }

// ---------- post list ----------
async function loadList() {
  const j = await api("/api/posts");
  $("list").innerHTML = "";
  for (const p of j.posts) {
    const d = document.createElement("div");
    d.className = "item" + (p.slug === slug ? " sel" : "");
    d.innerHTML = `<div></div><small></small>`;
    d.firstChild.textContent = p.title;
    d.lastChild.textContent = (p.date || "").slice(0, 10) + (p.inprogress ? " · in progress" : "") + (p.draft ? " · draft" : "");
    d.onclick = () => openPost(p.slug);
    $("list").appendChild(d);
  }
}
async function openPost(s) {
  if (dirty && !confirm("Discard unsaved changes?")) return;
  const j = await api("/api/post?slug=" + encodeURIComponent(s));
  slug = s; files = j.files; dirty = false; snaps = [];
  ed.disabled = false; ed.value = j.content;
  $("cur").textContent = s; setState("");
  location.hash = s;
  enterNormalIfVim(); render(); loadList(); ed.focus();
}
async function save() {
  if (!slug) return;
  try { await api("/api/post", {slug, content: ed.value}); dirty = false; setState("saved"); loadList(); }
  catch (e) { setState("save failed: " + e.message); }
}
window.addEventListener("beforeunload", e => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });

// ---------- markdown ----------
const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function url(u) {
  u = u.trim();
  if (/^(https?:|mailto:|#|\/\/|data:image)/i.test(u)) return u;
  if (u.startsWith("/")) return u;
  return "/files/" + encodeURIComponent(slug || "") + "/" + u.split("/").map(encodeURIComponent).join("/");
}
function inline(s) {
  const hold = [];
  const keep = h => "\u0000" + (hold.push(h) - 1) + "\u0000";
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, (_, c) => keep("<code>" + c + "</code>"));
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^)]*&quot;)?\)/g, (_, a, u) => keep(`<img alt="${a}" src="${url(u.replace(/&amp;/g, "&"))}">`));
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, t, u) => keep(`<a href="${url(u.replace(/&amp;/g, "&"))}" target="_blank" rel="noopener">${t}</a>`));
  s = s.replace(/\*\*([^*]+)\*\*|__([^_]+)__/g, (_, a, b) => "<strong>" + (a || b) + "</strong>");
  s = s.replace(/(^|[^*\w])\*([^*\s][^*]*)\*(?!\w)/g, "$1<em>$2</em>");
  s = s.replace(/(^|[^_\w])_([^_\s][^_]*)_(?!\w)/g, "$1<em>$2</em>");
  s = s.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => hold[+i]);
}
function md(src) {
  const L = src.replace(/\r/g, "").split("\n"), out = [];
  const isBlock = l => /^(```|#{1,6}\s|>|\s*([-*+]|\d+\.)\s|(-{3,}|\*{3,})\s*$)/.test(l);
  for (let i = 0; i < L.length;) {
    const l = L[i];
    let m;
    if ((m = l.match(/^```\s*(\S*)/))) {
      const buf = []; i++;
      while (i < L.length && !/^```/.test(L[i])) buf.push(L[i++]);
      i++;
      out.push(`<pre><code class="lang-${esc(m[1])}">${esc(buf.join("\n"))}</code></pre>`);
    } else if ((m = l.match(/^(#{1,6})\s+(.*?)\s*#*$/))) {
      out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); i++;
    } else if (/^(-{3,}|\*{3,})\s*$/.test(l)) { out.push("<hr>"); i++; }
    else if (/^>/.test(l)) {
      const buf = [];
      while (i < L.length && /^>/.test(L[i])) buf.push(L[i++].replace(/^>\s?/, ""));
      out.push("<blockquote>" + md(buf.join("\n")) + "</blockquote>");
    } else if (/^\s*([-*+]|\d+\.)\s+/.test(l)) {
      const ordered = /^\s*\d+\./.test(l), items = [];
      while (i < L.length && /^\s*([-*+]|\d+\.)\s+/.test(L[i])) {
        const mm = L[i].match(/^(\s*)(?:[-*+]|\d+\.)\s+(.*)$/);
        items.push(`<li style="margin-left:${Math.floor(mm[1].length / 2) * 1.2}em">${inline(mm[2])}</li>`); i++;
      }
      out.push(`<${ordered ? "ol" : "ul"}>${items.join("")}</${ordered ? "ol" : "ul"}>`);
    } else if (l.includes("|") && i + 1 < L.length && /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(L[i + 1])) {
      const cells = r => r.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map(c => inline(c.trim()));
      let h = "<table><thead><tr>" + cells(l).map(c => `<th>${c}</th>`).join("") + "</tr></thead><tbody>";
      i += 2;
      while (i < L.length && L[i].includes("|") && L[i].trim()) h += "<tr>" + cells(L[i++]).map(c => `<td>${c}</td>`).join("") + "</tr>";
      out.push(h + "</tbody></table>");
    } else if (!l.trim()) i++;
    else {
      const buf = [];
      while (i < L.length && L[i].trim() && (buf.length === 0 || !isBlock(L[i]))) buf.push(L[i++]);
      out.push("<p>" + buf.map(inline).join("<br>") + "</p>");
    }
  }
  return out.join("\n");
}
let rt = 0;
function render() { clearTimeout(rt); rt = setTimeout(renderNow, 80); }
function renderNow() {
  if (!slug) return;
  let t = ed.value, head = "";
  const m = t.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (m) { head = `<div class="fm">${esc(m[1]).replace(/\n/g, "<br>")}</div>`; t = t.slice(m[0].length); }
  prev.innerHTML = head + md(t);
}
function syncScroll() {
  const r = ed.scrollTop / Math.max(1, ed.scrollHeight - ed.clientHeight);
  prev.scrollTop = r * (prev.scrollHeight - prev.clientHeight);
}
ed.addEventListener("scroll", syncScroll);

// ---------- images ----------
function insertAtCursor(text) {
  const s = ed.selectionStart, e = ed.selectionEnd;
  ed.setRangeText(text, s, e, "end");
  changed();
}
async function uploadFiles(list) {
  if (!slug) return setState("open a post first");
  for (const f of list) {
    if (!f.type.startsWith("image/")) continue;
    let name = f.name;
    if (!name || name === "image.png") name = "image-" + Date.now() + "." + (f.type.split("/")[1] || "png").replace("svg+xml", "svg");
    try {
      const j = await api(`/api/image?slug=${encodeURIComponent(slug)}&name=${encodeURIComponent(name)}`, f, true);
      files.push(j.name);
      insertAtCursor(`![${j.name.replace(/\.[^.]+$/, "")}](${j.name})\n`);
      setState("uploaded " + j.name);
    } catch (e) { setState("upload failed: " + e.message); }
  }
}
ed.addEventListener("paste", e => {
  const imgs = [...e.clipboardData.files].filter(f => f.type.startsWith("image/"));
  if (imgs.length) { e.preventDefault(); uploadFiles(imgs); }
});
let dragN = 0;
const hasFiles = e => [...(e.dataTransfer?.types || [])].includes("Files");
$("edwrap").addEventListener("dragenter", e => { if (hasFiles(e)) { dragN++; $("drop").style.display = "flex"; } });
$("edwrap").addEventListener("dragleave", e => { if (hasFiles(e) && --dragN <= 0) { dragN = 0; $("drop").style.display = "none"; } });
$("edwrap").addEventListener("dragover", e => { if (hasFiles(e)) e.preventDefault(); });
$("edwrap").addEventListener("drop", e => {
  if (!hasFiles(e)) return;
  e.preventDefault(); dragN = 0; $("drop").style.display = "none";
  uploadFiles([...e.dataTransfer.files]);
});

// ---------- editor common ----------
function changed() { dirty = true; setState("unsaved"); render(); updPos(); }
function updPos() {
  const p = ed.selectionStart, b = ed.value.slice(0, p);
  const ln = b.split("\n").length, col = p - b.lastIndexOf("\n");
  $("pos").textContent = `${ln}:${col}`;
}
ed.addEventListener("input", () => { changed(); });
ed.addEventListener("keyup", updPos);
ed.addEventListener("click", updPos);
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); save(); }
});

// ---------- minimal vim ----------
let vim = localStorage.getItem("vim") === "1", mode = "insert", count = "", pend = "", cmd = null;
$("vimtoggle").checked = vim;
$("vimtoggle").onchange = () => { vim = $("vimtoggle").checked; localStorage.setItem("vim", vim ? "1" : "0"); vim ? setMode("normal") : setMode("insert"); ed.focus(); };
function setMode(m) {
  mode = m; count = pend = ""; cmd = null;
  ed.classList.toggle("normal", vim && m === "normal");
  $("mode").textContent = vim ? (m === "normal" ? "-- NORMAL --" : "-- INSERT --") : "";
  if (vim && m === "normal") showCursor();
  $("msg").textContent = "";
}
function enterNormalIfVim() { setMode(vim ? "normal" : "insert"); }
const V = () => ed.value;
const cur = () => ed.selectionStart;
const ls = p => V().lastIndexOf("\n", p - 1) + 1;
const le = p => { const i = V().indexOf("\n", p); return i < 0 ? V().length : i; };
function setCur(p) { p = Math.max(0, Math.min(p, V().length)); ed.setSelectionRange(p, p); showCursor(); }
function showCursor() {
  let p = cur();
  const end = le(p);
  if (p >= end && p > ls(p)) p = end - 1;       // normal mode sits on a char, not after it
  ed.setSelectionRange(p, V()[p] && V()[p] !== "\n" ? p + 1 : p);
  updPos();
}
function snap() { snaps.push([V(), cur()]); if (snaps.length > 200) snaps.shift(); }
function edit(fn) { snap(); fn(); changed(); }
function lineMove(p, n) {            // move n lines (neg = up) keeping column
  const col = p - ls(p);
  let s = ls(p);
  for (; n > 0; n--) { const e = le(s); if (e >= V().length) break; s = e + 1; }
  for (; n < 0; n++) { if (s === 0) break; s = ls(s - 1); }
  return Math.min(s + col, le(s));
}
const isW = c => /\w/.test(c);
function wordFwd(p) {
  const t = V(); if (p >= t.length) return p;
  const k = c => /\s/.test(c) ? 0 : isW(c) ? 1 : 2;
  const kind = k(t[p]); while (p < t.length && k(t[p]) === kind && kind) p++;
  while (p < t.length && /\s/.test(t[p])) p++;
  return p;
}
function wordBack(p) {
  const t = V(); if (p <= 0) return 0;
  p--; while (p > 0 && /\s/.test(t[p])) p--;
  const k = c => isW(c) ? 1 : 2, kind = k(t[p]);
  while (p > 0 && !/\s/.test(t[p - 1]) && k(t[p - 1]) === kind) p--;
  return p;
}
function delRange(a, b, linewise) {
  reg = V().slice(a, b); regLine = !!linewise;
  ed.setRangeText("", a, b, "start");
}
function runCmd(c) {
  if (c === "w") save();
  else if (c === "wq" || c === "x") save();
  else if (c === "q" || c === "q!") { if (dirty && c === "q") $("msg").textContent = "unsaved changes (use :q! or :w)"; else { slug = null; ed.value = ""; ed.disabled = true; prev.innerHTML = ""; $("cur").textContent = "no post open"; dirty = false; } }
  else $("msg").textContent = "not an editor command: " + c;
}
ed.addEventListener("keydown", e => {
  if (!vim) return;
  if (mode === "insert") {
    if (e.key === "Escape" || (e.ctrlKey && e.key === "[")) {
      e.preventDefault(); snap(); const p = cur(); setMode("normal"); setCur(p > ls(p) ? p - 1 : p);
    }
    return;
  }
  if (e.ctrlKey || e.metaKey || e.altKey) {
    if (e.ctrlKey && e.key === "r") e.preventDefault();
    return;                                   // let ctrl-s, ctrl-c etc through
  }
  e.preventDefault();
  const k = e.key;
  if (k === "Shift" || k === "Control" || k === "Alt") return;
  if (cmd !== null) {
    if (k === "Enter") { const c = cmd.trim(); setMode("normal"); runCmd(c); }
    else if (k === "Escape") setMode("normal");
    else if (k === "Backspace") { cmd = cmd.slice(0, -1); if (!cmd.length) { setMode("normal"); return; } $("msg").textContent = ":" + cmd; }
    else if (k.length === 1) { cmd += k; $("msg").textContent = ":" + cmd; }
    return;
  }
  if (k === "Escape") { count = pend = ""; $("msg").textContent = ""; return; }
  if (/^[1-9]$/.test(k) || (k === "0" && count)) { count += k; $("msg").textContent = count; return; }
  const n = parseInt(count || "1", 10); count = "";
  const p = cur();

  if (pend) {                                 // operator pending: d / y / g
    const op = pend; pend = ""; $("msg").textContent = "";
    if (op === "g") { if (k === "g") setCur(count ? 0 : 0); return; }
    const full = V();
    if (k === op) {                           // dd / yy (n lines)
      let a = ls(p), b = p; for (let i = 0; i < n; i++) b = Math.min(le(b) + 1, full.length);
      if (b >= full.length && a > 0 && op === "d") a--;     // last line: eat the preceding newline
      const txt = full.slice(a, b).replace(/^\n|\n$/g, "") + "\n";
      if (op === "d") { edit(() => delRange(a, b, true)); reg = txt; regLine = true; setCur(Math.min(ls(Math.min(a, V().length)) || a, V().length)); }
      else { reg = txt; regLine = true; $("msg").textContent = n + " line(s) yanked"; }
      return;
    }
    let q = p;
    if (k === "w") for (let i = 0; i < n; i++) q = wordFwd(q);
    else if (k === "b") for (let i = 0; i < n; i++) q = wordBack(q);
    else if (k === "$") q = le(p);
    else if (k === "0") q = ls(p);
    else return;
    const a = Math.min(p, q), b = Math.max(p, q);
    if (op === "d") { edit(() => delRange(a, b)); setCur(a); } else { reg = full.slice(a, b); regLine = false; }
    return;
  }

  switch (k) {
    case "h": case "ArrowLeft": setCur(Math.max(ls(p), p - n)); break;
    case "l": case "ArrowRight": setCur(Math.min(le(p) - 1, p + n)); break;
    case "j": case "ArrowDown": setCur(lineMove(p, n)); break;
    case "k": case "ArrowUp": setCur(lineMove(p, -n)); break;
    case "w": { let q = p; for (let i = 0; i < n; i++) q = wordFwd(q); setCur(q); break; }
    case "b": { let q = p; for (let i = 0; i < n; i++) q = wordBack(q); setCur(q); break; }
    case "0": setCur(ls(p)); break;
    case "^": { let q = ls(p); while (V()[q] === " " || V()[q] === "\t") q++; setCur(q); break; }
    case "$": setCur(Math.max(ls(p), le(p) - 1)); break;
    case "G": setCur(ls(V().length)); ed.scrollTop = ed.scrollHeight; break;
    case "g": case "d": case "y": pend = k; $("msg").textContent = k; if (n > 1) count = String(n); break;
    case "i": setMode("insert"); break;
    case "a": setMode("insert"); ed.setSelectionRange(Math.min(p + 1, le(p)), Math.min(p + 1, le(p))); break;
    case "I": { setMode("insert"); const q = ls(p); ed.setSelectionRange(q, q); break; }
    case "A": { setMode("insert"); const q = le(p); ed.setSelectionRange(q, q); break; }
    case "o": { snap(); const q = le(p); ed.setRangeText("\n", q, q, "end"); setMode("insert"); changed(); break; }
    case "O": { snap(); const q = ls(p); ed.setRangeText("\n", q, q, "start"); setMode("insert"); changed(); break; }
    case "x": if (p < le(p)) { edit(() => delRange(p, Math.min(p + n, le(p)))); setCur(p); } break;
    case "D": edit(() => delRange(p, le(p))); setCur(p - 1 >= ls(p) ? p - 1 : p); break;
    case "p": case "P": {
      if (!reg) break;
      edit(() => {
        if (regLine) { const q = k === "p" ? Math.min(le(p) + 1, V().length) : ls(p);
          let t = reg; if (k === "p" && le(p) >= V().length) t = "\n" + t.replace(/\n$/, "");
          ed.setRangeText(t, q, q, "start"); }
        else { const q = k === "p" ? Math.min(p + 1, le(p)) : p; ed.setRangeText(reg.repeat(n), q, q, "end"); }
      });
      setCur(regLine ? Math.min(le(p) + 1, V().length) : cur()); break;
    }
    case "u": { const s = snaps.pop(); if (s) { ed.value = s[0]; changed(); setCur(s[1]); } else $("msg").textContent = "already at oldest change"; break; }
    case ":": cmd = ""; $("msg").textContent = ":"; break;
    default: break;
  }
});

// ---------- new post / publish ----------
const slugify = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
let slugTouched = false;
$("n_title").oninput = () => { if (!slugTouched) $("n_slug").value = slugify($("n_title").value); };
$("n_slug").oninput = () => { slugTouched = true; };
$("newbtn").onclick = () => { slugTouched = false; $("newform").reset(); $("newdlg").showModal(); };
$("n_cancel").onclick = () => $("newdlg").close();
$("n_ok").onclick = async e => {
  e.preventDefault();
  if (!$("newform").reportValidity()) return;
  if (dirty && !confirm("Discard unsaved changes?")) return;
  try {
    const j = await api("/api/new", {title: $("n_title").value, slug: $("n_slug").value, description: $("n_desc").value, tags: $("n_tags").value});
    $("newdlg").close(); dirty = false; await openPost(j.slug);
    ed.focus(); setCur(V().length);
    if (vim) { setMode("insert"); ed.setSelectionRange(V().length, V().length); }
  } catch (err) { alert(err.message); }
};
$("savebtn").onclick = save;
$("pubbtn").onclick = () => { if (!slug) return; $("log").hidden = true; $("p_msg").value = "Add post " + slug; $("pubdlg").showModal(); };
$("p_cancel").onclick = () => $("pubdlg").close();
$("p_ok").onclick = async e => {
  e.preventDefault();
  if (!confirm("This pushes to the remote. Continue?")) return;
  await save();
  $("p_ok").disabled = true;
  try {
    const j = await api("/api/publish", {slug, message: $("p_msg").value});
    $("log").hidden = false; $("log").textContent = j.log;
  } catch (err) { $("log").hidden = false; $("log").textContent = err.message; }
  $("p_ok").disabled = false;
};

// ---------- boot ----------
setMode(vim ? "normal" : "insert");
loadList().then(() => { if (location.hash.length > 1) openPost(decodeURIComponent(location.hash.slice(1))).catch(() => {}); });
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
