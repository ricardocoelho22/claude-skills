// Renders the feature hub and its linked pages from data.json.
// The pages are fixed; a refresh changes only data.json and the copied sources.
(function () {
  "use strict";

  var LABELS = {
    "done": "Done", "in-progress": "In progress", "needs-you": "Needs you", "open": "Open", "deferred": "Deferred", "dropped": "Dropped",
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

  // Deferred and dropped tickets are set aside: shown, but left out of progress and slice status.
  function setAside(t) { return t.status === "deferred" || t.status === "dropped"; }
  function active(tickets) { return (tickets || []).filter(function (t) { return !setAside(t); }); }

  function sliceStatus(s) {
    var all = s.tickets || [];
    if (!all.length) return s.specPath ? "no-tickets" : "planned";
    var t = active(all);
    if (!t.length) return all.some(function (x) { return x.status === "deferred"; }) ? "deferred" : "dropped";
    var n = function (st) { return t.filter(function (x) { return x.status === st; }).length; };
    if (n("done") === t.length) return "done";
    if (n("needs-you")) return "needs-you";
    if (n("in-progress") || n("done")) return "in-progress";
    return "not-started";
  }
  function allTickets() {
    return data.slices.reduce(function (acc, s) { return acc.concat(s.tickets || []); }, []);
  }

  // Markdown: rendered with marked. Raw HTML in a source shows as text, mermaid fences become
  // diagrams, and links to files that are not published become plain text.
  if (window.marked) {
    window.marked.use({ renderer: { html: function (h) { return esc(typeof h === "object" ? h.text : h); } } });
  }
  function md(text) {
    var html = window.marked ? window.marked.parse(text || "") : "<pre>" + esc(text) + "</pre>";
    return tidy(html);
  }
  // One-line fields (titles, purposes, gists) take inline markdown only.
  function inline(text) {
    return window.marked ? tidy(window.marked.parseInline(String(text == null ? "" : text))) : esc(text);
  }
  // Text for the browser tab: inline markdown with the marks removed.
  function plain(text) {
    var box = document.createElement("div");
    box.innerHTML = inline(text);
    return box.textContent;
  }
  function tidy(html) {
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
      var extra = t.checklist ? ' &middot; <a href="doc.html#' + esc(t.checklist) + '">checks</a>' : "";
      return '<li class="' + (t.status === "done" || setAside(t) ? "is-done" : "") + (t.status === "dropped" ? " is-dropped" : "") + '"><span class="tnum">#' + esc(t.num) + "</span>" +
        '<span class="ttitle">' + inline(t.title) + extra + "</span>" + chip(t.status) + "</li>";
    };
    var open = active(tickets).filter(function (t) { return t.status !== "done"; });
    var done = tickets.filter(function (t) { return t.status === "done"; });
    var aside = tickets.filter(setAside);
    var html = open.length ? '<ul class="tickets">' + open.map(row).join("") + "</ul>" : "";
    if (done.length) {
      var list = '<ul class="tickets">' + done.map(row).join("") + "</ul>";
      html += open.length
        ? '<details class="closed-group"><summary>' + done.length + " done</summary>" + list + "</details>"
        : list;
    }
    if (aside.length) {
      html += '<details class="closed-group"><summary>' + aside.length + " deferred or dropped</summary>" +
        '<ul class="tickets">' + aside.map(row).join("") + "</ul></details>";
    }
    return html || '<p class="empty">No tickets yet.</p>';
  }

  function renderHub() {
    var everything = allTickets();
    var tickets = active(everything);
    var asideCount = everything.length - tickets.length;
    var count = function (st) { return tickets.filter(function (t) { return t.status === st; }).length; };
    var total = tickets.length || 1;
    var bar = ["done", "in-progress", "needs-you"].map(function (st) {
      return count(st) ? '<span class="' + st + '" style="width:' + (100 * count(st) / total) + '%"></span>' : "";
    }).join("");

    var html = '<header><span class="eyebrow">Feature</span><h1>' + esc(data.feature) + "</h1>" +
      '<p class="destination">' + inline(data.destination) + "</p>" +
      '<div class="progress" role="img" aria-label="' + count("done") + " of " + tickets.length + ' tickets done">' + bar + "</div>" +
      '<div class="meta"><span>' + count("done") + " of " + tickets.length + " tickets done" +
      (asideCount ? " (" + asideCount + " deferred or dropped)" : "") + "</span><span>" +
      data.slices.length + (data.slices.length === 1 ? " slice" : " slices") + "</span><span>Updated " + esc(data.builtAt) + "</span></div></header>";

    if ((data.waiting || []).length) {
      html += '<section class="waiting" aria-labelledby="w"><h2 id="w">Waiting on you</h2><ul>' +
        data.waiting.map(function (w) {
          return "<li>" + inline(w.text) + (w.href ? ' <a href="' + esc(w.href) + '">Open</a>' : "") + "</li>";
        }).join("") + "</ul></section>";
    }
    if (data.intro) html += '<section><h2>About this feature</h2><div class="prose">' + md(data.intro) + "</div></section>";
    if (data.architecture) html += '<section id="architecture"><h2>Architecture</h2><div class="prose">' + md(data.architecture) + "</div></section>";

    html += '<section id="slices"><h2>Slices</h2><div class="ledger">' + data.slices.map(function (s, i) {
      var st = sliceStatus(s);
      var t = active(s.tickets);
      var done = t.filter(function (x) { return x.status === "done"; }).length;
      var openAttr = data.slices.length === 1 || st === "in-progress" || st === "needs-you" ? " open" : "";
      return "<details" + openAttr + "><summary>" +
        '<span class="num">' + String(i + 1).padStart(2, "0") + "</span>" +
        '<span class="title">' + inline(s.title) + "</span>" +
        '<span class="side">' + chip(st) + '<span class="count">' + done + "/" + t.length + "</span></span>" +
        '<span class="purpose">' + inline(s.purpose) + "</span></summary>" +
        '<div class="body">' + ticketList(s.tickets || []) +
        (s.summary ? '<a href="slice.html#' + esc(s.id) + '">Read the slice summary</a>' : '<span class="muted">No summary yet.</span>') +
        "</div></details>";
    }).join("") + "</div></section>";

    var decisions = data.decisions || [];
    if (decisions.length) {
      var latest = decisions.slice(-5).reverse();
      html += '<section id="decisions"><h2>Recent decisions</h2><ul class="list">' + latest.map(function (d) {
        return "<li><strong>" + inline(d.title) + '</strong><span class="gist">' + inline(d.gist) + "</span></li>";
      }).join("") + "</ul>" +
        (decisions.length > latest.length ? '<a href="doc.html#decisions">All ' + decisions.length + " decisions</a>" : "") + "</section>";
    }
    if ((data.experiments || []).length) {
      html += '<section id="experiments"><h2>Experiments</h2><ul class="list">' + data.experiments.map(function (x) {
        var title = x.href ? '<a href="' + esc(x.href) + '">' + inline(x.title) + "</a>" : "<strong>" + inline(x.title) + "</strong>";
        return "<li>" + title +
          (x.summary ? '<span class="gist">' + inline(x.summary) + "</span>" : "") +
          (x.result ? '<span class="result"><span class="label">Result</span> ' + inline(x.result) + "</span>" : "") +
          (!x.href && x.source ? '<span class="mono muted">' + esc(x.source) + "</span>" : "") + "</li>";
      }).join("") + "</ul></section>";
    }
    if ((data.links || []).length) {
      html += '<section id="links"><h2>Related</h2><ul class="list">' + data.links.map(function (l) {
        return "<li>" + (l.href ? '<a href="' + esc(l.href) + '">' + inline(l.title) + "</a>" : "<strong>" + inline(l.title) + "</strong>") + (l.note ? '<span class="gist">' + inline(l.note) + "</span>" : "") + "</li>";
      }).join("") + "</ul></section>";
    }
    root.innerHTML = html + footer();
    document.title = plain(data.feature);
    drawDiagrams();
  }

  function renderSlice() {
    var id = location.hash.slice(1);
    var idx = data.slices.findIndex(function (s) { return s.id === id; });
    var s = data.slices[idx];
    var back = '<a class="back" href="./">Back to ' + esc(data.feature) + "</a>";
    if (!s) { root.innerHTML = back + '<p class="empty">This slice is not in the feature.</p>'; return; }
    root.innerHTML = back +
      '<header><span class="eyebrow">Slice ' + String(idx + 1).padStart(2, "0") + "</span><h1>" + inline(s.title) + "</h1>" +
      '<p class="destination">' + inline(s.purpose) + "</p><div>" + chip(sliceStatus(s)) + "</div></header>" +
      '<section><h2>Summary</h2><div class="prose">' +
      (s.summary ? md(s.summary) : '<p class="empty">No summary yet.</p>') + "</div>" +
      (s.specPath ? '<p class="muted">The full spec is <span class="mono">' + esc(s.specPath) + "</span>.</p>" : "") + "</section>" +
      "<section><h2>Tickets</h2>" + ticketList(s.tickets || []) + "</section>" + footer();
    document.title = plain(s.title) + " \u00b7 " + plain(data.feature);
    drawDiagrams();
  }

  function renderDoc() {
    var id = location.hash.slice(1);
    var back = '<a class="back" href="./">Back to ' + esc(data.feature) + "</a>";
    if (id === "decisions") {
      root.innerHTML = back + '<header><span class="eyebrow">Decisions</span><h1>Decisions so far</h1></header><ul class="list">' +
        (data.decisions || []).map(function (d) {
          return "<li><strong>" + inline(d.title) + '</strong><span class="gist">' + inline(d.gist) + "</span></li>";
        }).join("") + "</ul>" + footer();
      document.title = "Decisions \u00b7 " + plain(data.feature);
      return;
    }
    var doc = (data.docs || {})[id];
    if (!doc) { root.innerHTML = back + '<p class="empty">This document is not in the feature.</p>'; return; }
    root.innerHTML = back + '<header><span class="eyebrow">' + esc(doc.kind || "Document") + "</span><h1>" + inline(doc.title) + "</h1></header>" +
      '<div class="prose" id="doc"><p class="empty">Loading.</p></div>' + footer();
    document.title = plain(doc.title) + " \u00b7 " + plain(data.feature);
    fetchText(doc.src).then(function (text) {
      var box = document.getElementById("doc");
      box.innerHTML = md(text);
      if (box.firstElementChild && box.firstElementChild.tagName === "H1") box.firstElementChild.remove();
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
