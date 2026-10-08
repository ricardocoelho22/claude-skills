// Renders the feature hub and its linked pages from data.json.
// The pages are fixed; a refresh changes only data.json and the copied sources.
(function () {
  "use strict";

  var LABELS = {
    "done": "Done", "in-progress": "In progress", "needs-info": "Needs you", "open": "Open",
    "not-started": "Not started", "no-tickets": "No tickets yet", "planned": "Planned"
  };
  var root = document.getElementById("app");
  var data = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function chip(status) { return '<span class="chip ' + esc(status) + '">' + esc(LABELS[status] || status) + "</span>"; }

  function sliceStatus(s) {
    var t = s.tickets || [];
    if (!t.length) return s.specPath ? "no-tickets" : "planned";
    var n = function (st) { return t.filter(function (x) { return x.status === st; }).length; };
    if (n("done") === t.length) return "done";
    if (n("needs-info")) return "needs-info";
    if (n("in-progress") || n("done")) return "in-progress";
    return "not-started";
  }
  function allTickets() {
    return data.slices.reduce(function (acc, s) { return acc.concat(s.tickets || []); }, []);
  }

  // Markdown: rendered with marked; mermaid fences become diagrams; links to unpublished files become plain text.
  function md(text) {
    var html = window.marked ? window.marked.parse(text || "") : "<pre>" + esc(text) + "</pre>";
    var box = document.createElement("div");
    box.innerHTML = html;
    box.querySelectorAll("pre > code.language-mermaid").forEach(function (code) {
      var pre = document.createElement("pre");
      pre.className = "mermaid";
      pre.textContent = code.textContent;
      code.parentNode.replaceWith(pre);
    });
    box.querySelectorAll("a[href]").forEach(function (a) {
      var href = a.getAttribute("href");
      if (/^(https?:|#)/.test(href)) return;
      var page = href.split("#")[0];
      if ((data.published || []).indexOf(page) !== -1) return;
      var span = document.createElement("span");
      span.className = "dead-link";
      span.title = href + " is not part of this page";
      span.innerHTML = a.innerHTML;
      a.replaceWith(span);
    });
    return box.innerHTML;
  }
  function drawDiagrams() {
    var pending = document.querySelectorAll("pre.mermaid:not([data-processed])");
    if (!pending.length) return;
    var run = function () {
      var dark = matchMedia("(prefers-color-scheme: dark)").matches && document.documentElement.dataset.theme !== "light";
      if (document.documentElement.dataset.theme === "dark") dark = true;
      window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral" });
      window.mermaid.run({ nodes: pending });
    };
    if (window.mermaid) return run();
    var s = document.createElement("script");
    s.src = "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js";
    s.onload = run;
    document.head.appendChild(s);
  }
  function fetchText(src) {
    return fetch(src, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(src + " returned " + r.status);
      return r.text();
    });
  }

  function footer() {
    return '<footer><span>Built from <span class="mono">' + esc(data.source) + "</span> on " + esc(data.builtAt) + ".</span>" +
      "<span>This page is a view. Change the files, then refresh it.</span></footer>";
  }

  function ticketList(tickets) {
    var row = function (t) {
      var extra = t.checklist ? ' · <a href="doc.html#' + esc(t.checklist) + '">checks</a>' : "";
      return '<li class="' + (t.status === "done" ? "is-done" : "") + '"><span class="tnum">#' + esc(t.num) + "</span>" +
        '<span class="ttitle">' + esc(t.title) + extra + "</span>" + chip(t.status) + "</li>";
    };
    var open = tickets.filter(function (t) { return t.status !== "done"; });
    var done = tickets.filter(function (t) { return t.status === "done"; });
    var html = open.length ? '<ul class="tickets">' + open.map(row).join("") + "</ul>" : "";
    if (done.length) {
      var list = '<ul class="tickets">' + done.map(row).join("") + "</ul>";
      html += open.length
        ? '<details class="closed-group"><summary>' + done.length + " done</summary>" + list + "</details>"
        : list;
    }
    return html || '<p class="empty">No tickets yet.</p>';
  }

  function renderHub() {
    var tickets = allTickets();
    var count = function (st) { return tickets.filter(function (t) { return t.status === st; }).length; };
    var total = tickets.length || 1;
    var bar = ["done", "in-progress", "needs-info"].map(function (st) {
      return count(st) ? '<span class="' + st + '" style="width:' + (100 * count(st) / total) + '%"></span>' : "";
    }).join("");

    var html = '<header><span class="eyebrow">Feature</span><h1>' + esc(data.feature) + "</h1>" +
      '<p class="destination">' + esc(data.destination) + "</p>" +
      '<div class="progress" role="img" aria-label="' + count("done") + " of " + tickets.length + ' tickets done">' + bar + "</div>" +
      '<div class="meta"><span>' + count("done") + " of " + tickets.length + " tickets done</span><span>" +
      data.slices.length + (data.slices.length === 1 ? " slice" : " slices") + "</span><span>Updated " + esc(data.builtAt) + "</span></div></header>";

    if ((data.waiting || []).length) {
      html += '<section class="waiting" aria-labelledby="w"><h2 id="w">Waiting on you</h2><ul>' +
        data.waiting.map(function (w) {
          return "<li>" + (w.href ? '<a href="' + esc(w.href) + '">' + esc(w.text) + "</a>" : esc(w.text)) + "</li>";
        }).join("") + "</ul></section>";
    }
    if (data.intro) html += '<section><h2>About this feature</h2><div class="prose short">' + md(data.intro) + "</div></section>";
    if (data.architecture) html += '<section id="architecture"><h2>Architecture</h2><div class="prose">' + md(data.architecture) + "</div></section>";

    html += '<section id="slices"><h2>Slices</h2><div class="ledger">' + data.slices.map(function (s, i) {
      var st = sliceStatus(s);
      var t = s.tickets || [];
      var done = t.filter(function (x) { return x.status === "done"; }).length;
      var openAttr = data.slices.length === 1 || st === "in-progress" || st === "needs-info" ? " open" : "";
      return "<details" + openAttr + "><summary>" +
        '<span class="num">' + String(i + 1).padStart(2, "0") + "</span>" +
        '<span class="title">' + esc(s.title) + "</span>" +
        '<span class="side">' + chip(st) + '<span class="count">' + done + "/" + t.length + "</span></span>" +
        '<span class="purpose">' + esc(s.purpose) + "</span></summary>" +
        '<div class="body">' + ticketList(t) +
        (s.summary ? '<a href="slice.html#' + esc(s.id) + '">Read the slice summary</a>' : '<span class="muted">No summary yet.</span>') +
        "</div></details>";
    }).join("") + "</div></section>";

    var decisions = data.decisions || [];
    if (decisions.length) {
      var latest = decisions.slice(-5).reverse();
      html += '<section id="decisions"><h2>Recent decisions</h2><ul class="list">' + latest.map(function (d) {
        return "<li><strong>" + esc(d.title) + '</strong><span class="gist">' + esc(d.gist) + "</span></li>";
      }).join("") + "</ul>" +
        (decisions.length > latest.length ? '<a href="doc.html#decisions">All ' + decisions.length + " decisions</a>" : "") + "</section>";
    }
    if ((data.links || []).length) {
      html += '<section id="links"><h2>Related</h2><ul class="list">' + data.links.map(function (l) {
        return '<li><a href="' + esc(l.href) + '">' + esc(l.title) + "</a>" + (l.note ? '<span class="gist">' + esc(l.note) + "</span>" : "") + "</li>";
      }).join("") + "</ul></section>";
    }
    root.innerHTML = html + footer();
    document.title = data.feature;
    drawDiagrams();
  }

  function renderSlice() {
    var id = location.hash.slice(1);
    var idx = data.slices.findIndex(function (s) { return s.id === id; });
    var s = data.slices[idx];
    var back = '<a class="back" href="./">Back to ' + esc(data.feature) + "</a>";
    if (!s) { root.innerHTML = back + '<p class="empty">This slice is not in the feature.</p>'; return; }
    root.innerHTML = back +
      '<header><span class="eyebrow">Slice ' + String(idx + 1).padStart(2, "0") + "</span><h1>" + esc(s.title) + "</h1>" +
      '<p class="destination">' + esc(s.purpose) + "</p><div>" + chip(sliceStatus(s)) + "</div></header>" +
      '<section><h2>Summary</h2><div class="prose short">' +
      (s.summary ? md(s.summary) : '<p class="empty">No summary yet.</p>') + "</div>" +
      (s.specPath ? '<p class="muted">The full spec is <span class="mono">' + esc(s.specPath) + "</span>.</p>" : "") + "</section>" +
      "<section><h2>Tickets</h2>" + ticketList(s.tickets || []) + "</section>" + footer();
    document.title = s.title + " · " + data.feature;
    drawDiagrams();
  }

  function renderDoc() {
    var id = location.hash.slice(1);
    var back = '<a class="back" href="./">Back to ' + esc(data.feature) + "</a>";
    if (id === "decisions") {
      root.innerHTML = back + '<header><span class="eyebrow">Decisions</span><h1>Decisions so far</h1></header><ul class="list">' +
        (data.decisions || []).map(function (d) {
          return "<li><strong>" + esc(d.title) + '</strong><span class="gist">' + esc(d.gist) + "</span></li>";
        }).join("") + "</ul>" + footer();
      document.title = "Decisions · " + data.feature;
      return;
    }
    var doc = (data.docs || {})[id];
    if (!doc) { root.innerHTML = back + '<p class="empty">This document is not in the feature.</p>'; return; }
    root.innerHTML = back + '<header><span class="eyebrow">' + esc(doc.kind || "Document") + "</span><h1>" + esc(doc.title) + "</h1></header>" +
      '<div class="prose" id="doc"><p class="empty">Loading.</p></div>' + footer();
    document.title = doc.title + " · " + data.feature;
    fetchText(doc.src).then(function (text) {
      document.getElementById("doc").innerHTML = md(text);
      drawDiagrams();
    }).catch(function (e) { document.getElementById("doc").innerHTML = '<p class="empty">' + esc(e.message) + "</p>"; });
  }

  var render = { hub: renderHub, slice: renderSlice, doc: renderDoc }[root.dataset.page] || renderHub;
  fetch("data.json", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    render();
    addEventListener("hashchange", render);
  }).catch(function () {
    root.innerHTML = '<p class="empty">The feature data did not load. Refresh the feature to publish it again.</p>';
  });
})();
