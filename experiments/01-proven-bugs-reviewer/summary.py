#!/usr/bin/env python3
"""Per-arm numbers for the decision rule, computed from the raw rows only.

  summary.py --raw <dir>

Reads reviews.jsonl, graded/*.json, grader.jsonl. Prints JSON.
"seeds hit": distinct (review, seed) hits by a finding tagged Important or Nit (Pre-existing
findings never count as hits); real and synthetic apart. "False above Nit": non-hit Important
findings with verdict false (unsure and real-but-unseeded reported apart). Pre-existing counted apart.
"""
import argparse, json, statistics, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))
LEAK_PATHS = ["z-features", "docs/experiments", "proven-bugs-reviewer", "sidedoor-backend", "answer-keys"]
GIT_HASH_CMD = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?(diff|show|log|cat-file|rev-list|checkout|reset|ls-tree)\b([^|;&\n]*)")
GIT_ALL = re.compile(r"\bgit\b[^|;&\n]*\blog\b[^|;&\n]*(--all|--branches|--remotes)|\bgit\b[^|;&\n]*\b(branch|tag|reflog|for-each-ref)\b")
PROOF_CMD = re.compile(r"\b(jest|vitest|pnpm|npm|npx|yarn|tsx|ts-node|node|python3?|tsc|bash|sh)\b")


def trace(raw, row):
    """Tool calls of one review from its saved stream-json transcript.
    Returns leak_suspect (list of reasons), proof_runs (test/script Bash commands with exit codes),
    tool_counts, writes (Write/Edit targets)."""
    path = f"{raw}/{row['transcript_file']}" if row.get("transcript_file") else None
    if not path or not os.path.exists(path):
        return None
    base = CFG["tickets"][row["ticket"]]["base"]
    calls, results = [], {}
    for line in open(path):
        try:
            e = json.loads(line)
        except Exception:
            continue
        m_ = e.get("message")
        c = m_.get("content") if isinstance(m_, dict) else None
        if e.get("type") not in ("assistant", "user") or not isinstance(c, list):
            continue
        for b in c:
            if b.get("type") == "tool_use":
                calls.append(b)
            elif b.get("type") == "tool_result":
                results[b["tool_use_id"]] = b
    leak, proofs, counts, writes = [], [], {}, []
    for b in calls:
        name, inp = b["name"], b.get("input") or {}
        counts[name] = counts.get(name, 0) + 1
        # leak match on tool-call inputs that name a command or a path only, never on file text or outputs
        text = json.dumps({k: v for k, v in inp.items() if k in ("command", "file_path", "path", "pattern", "glob", "notebook_path")})
        for p in LEAK_PATHS:
            if p in text:
                leak.append(f"{name} touches {p}: {text[:160]}")
        if name == "Bash":
            cmd = inp.get("command", "")
            if GIT_ALL.search(cmd):
                leak.append(f"git all-refs: {cmd[:160]}")
            for m in GIT_HASH_CMD.finditer(cmd):
                for h in re.findall(r"(?<![\w.-])[0-9a-f]{7,40}(?![\w-])", m.group(2)):
                    if not (h.startswith(base) or base.startswith(h)):
                        leak.append(f"git {m.group(1)} {h}: {cmd[:160]}")
            if PROOF_CMD.search(cmd) and not re.match(r"\s*(git|rg|ls|cat|head|tail|wc|grep|find|sed|nl)\b", cmd):
                r = results.get(b["id"], {})
                content = r.get("content")
                if isinstance(content, list):
                    content = " ".join(x.get("text", "") for x in content if isinstance(x, dict))
                m = re.match(r"Exit code (\d+)", content or "")
                js = re.findall(r"^\s*Tests:.*$", content or "", re.M)
                proofs.append({"command": cmd[:300], "exit_code": int(m.group(1)) if m else (None if not r else 0),
                               "jest_tests_line": js[-1].strip() if js else None})
        if name in ("Write", "Edit"):
            writes.append(inp.get("file_path"))
    return {"leak_suspect": leak, "proof_runs": proofs, "tool_counts": counts, "writes": writes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    raw = os.path.abspath(ap.parse_args().raw)
    rows = [json.loads(l) for l in open(f"{raw}/reviews.jsonl")]
    by_review = {}
    for r in rows:
        by_review.setdefault(r["id"], []).append(r)
    graded = [json.load(open(p)) for p in sorted(glob.glob(f"{raw}/graded/*.json"))]
    kind = {}
    for g in graded:
        for k in g["keys"]:
            kind[(g["ticket"], g["condition"], k["id"])] = k["kind"]
    out = {}
    for arm in ("A", "B"):
        arm_rows = [r for r in rows if r["arm"] == arm]
        ok = [r for r in arm_rows if r["status"] == "ok"]
        usage = {}
        for r in arm_rows:
            for k, v in (r.get("usage") or {}).items():
                if isinstance(v, (int, float)):
                    usage[k] = usage.get(k, 0) + v
            tt = ((r.get("usage") or {}).get("output_tokens_details") or {}).get("thinking_tokens")
            if tt:
                usage["thinking_tokens"] = usage.get("thinking_tokens", 0) + tt
        hits = {"real": set(), "synthetic": set()}
        hits_above_nit = {"real": set(), "synthetic": set()}
        c = {"findings": 0, "important": 0, "nit": 0, "pre_existing": 0, "false_above_nit": 0,
             "unsure_above_nit": 0, "real_unseeded_above_nit": 0, "false_nit": 0}
        for g in graded:
            for f in g["findings"]:
                if not f["review"].startswith(arm + "-"):
                    continue
                c["findings"] += 1
                tag = f["tag"]
                if tag == "Important": c["important"] += 1
                elif tag == "Nit": c["nit"] += 1
                elif tag == "Pre-existing": c["pre_existing"] += 1
                if f["verdict"] == "hit" and tag != "Pre-existing" and f["hit_seed"]:
                    kd = kind[(g["ticket"], g["condition"], f["hit_seed"])]
                    hits[kd].add((f["review"], f["hit_seed"]))
                    if tag == "Important":
                        hits_above_nit[kd].add((f["review"], f["hit_seed"]))
                elif f["verdict"] != "hit" and tag == "Important":
                    c[{"false": "false_above_nit", "unsure": "unsure_above_nit",
                       "real-but-unseeded": "real_unseeded_above_nit"}[f["verdict"]]] += 1
                elif f["verdict"] == "false" and tag == "Nit":
                    c["false_nit"] += 1
        walls = [r["wall_s"] for r in ok]
        per_review = {}
        for r in ok:
            t = trace(raw, r) or {}
            per_review[r["id"]] = {
                "leak_suspect": t.get("leak_suspect"), "tool_counts": t.get("tool_counts"),
                **({"proof_runs": t["proof_runs"], "writes": t["writes"]} if arm == "B" and t else {}),
                "wall_attempts_s": r.get("wall_attempts_s"),
                "model_ids": r.get("model_ids"), "model": r.get("model"),
                "model_mismatch": sorted(set(r.get("model_ids") or []) - {CFG["expected_model"]}) or (
                    None if r.get("model_ids") else ["no model recorded"])}
        out[arm] = {
            "reviews_ok": len(ok), "reviews_failed": len([r for r in arm_rows if r["status"] == "failed"]),
            "retries": sum(r.get("retries") or 0 for r in arm_rows),
            "seeds_hit_real": len(hits["real"]), "seeds_hit_synthetic": len(hits["synthetic"]),
            "seeds_hit_above_nit_real": len(hits_above_nit["real"]),
            "seeds_hit_above_nit_synthetic": len(hits_above_nit["synthetic"]),
            **c,
            "median_wall_s": statistics.median(walls) if walls else None,
            "wall_s": walls, "cost_usd": round(sum(r.get("cost_usd") or 0 for r in arm_rows), 4),
            "usage_sums": usage, "reviews": per_review,
            "reviews_leak_suspect": [k for k, v in per_review.items() if v["leak_suspect"]],
            "reviews_model_mismatch": [k for k, v in per_review.items() if v["model_mismatch"]],
        }
    g_rows = [json.loads(l) for l in open(f"{raw}/grader.jsonl")] if os.path.exists(f"{raw}/grader.jsonl") else []
    out["grader"] = {"calls": len(g_rows), "failed": sum(1 for g in g_rows if g["exit_code"]),
                     "tokens_used": sum(g.get("tokens_used") or 0 for g in g_rows),
                     "wall_s": round(sum(g["wall_s"] for g in g_rows), 1)}
    out["total_cost_usd"] = round(sum(out[a]["cost_usd"] for a in ("A", "B")), 4)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
