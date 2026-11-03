#!/usr/bin/env python3
"""Review runner: one `claude -p` call per (arm, ticket, condition, rep).

  run_reviews.py --raw <dir> --tickets 29 --conditions seeded --reps 1 [--seed 1] [--dry-run]

Writes <raw>/reviews.jsonl (one row per call), <raw>/reviews/<id>.md (reviewer text),
<raw>/claude-json/<id>-try<n>.{json,jsonl} (result event, full stream). Appends; ids already ok are skipped
(so a re-run to the same folder resumes instead of duplicating).

Permissions (identical in both arms: project settings only, OS sandbox on, auto-allow Bash inside
the sandbox, acceptEdits): file writes are confined by the sandbox to cwd (the scratch copy) and
/tmp (mongodb-memory-server needs its unix socket there); network is only the model's. Reads of
the answer-bearing paths (CFG leak_denied_paths) are denied by a permissions.deny Read rule and a
sandbox filesystem.denyRead. The arms differ only in the role file's tools line and read-only /
scratch-copy paragraph, and B's brief suffix (the variable under test).
Transcript: --output-format stream-json --verbose; the full stream is saved per attempt as
<id>-try<n>.jsonl, the final result event as <id>-try<n>.json.
"""
import argparse, json, os, random, subprocess, sys, threading, time, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prep

CFG = prep.CFG
SYSTEM_AGENT = "exp-reviewer"  # same name both arms; never the ~/.claude/agents one
DENY = CFG["leak_denied_paths"]
SETTINGS = {
    "permissions": {"deny": [f"Read(/{p}/**)" for p in DENY]},  # leading // = absolute path
    "sandbox": {
        "enabled": True, "autoAllowBashIfSandboxed": True, "allowUnsandboxedCommands": False,
        "network": {"allowLocalBinding": True, "allowAllUnixSockets": True},
        "filesystem": {"allowWrite": ["/tmp", "/private/tmp"], "denyRead": list(DENY)},
    },
}


def parse_agent(path):
    txt = open(path).read()
    _, fm, body = txt.split("---\n", 2)
    meta = dict(l.split(": ", 1) for l in fm.strip().split("\n"))
    return {
        "description": meta["description"],
        "prompt": body.strip(),
        "tools": [t.strip() for t in meta["tools"].split(",")],
        "model": meta["model"],
    }


def agents_json(arm):
    return json.dumps({SYSTEM_AGENT: parse_agent(f"{HERE}/agents/{arm}-rc-reviewer.md")})


def brief(arm):
    return open(f"{HERE}/agents/{arm}-brief.txt").read().strip()


def prompt_for(arm, ticket, wt):
    base = CFG["tickets"][ticket]["base"]
    return (
        f"Review the uncommitted changes in this working tree.\n"
        f"Diff command: `git diff {base}`\n"
        f"Ticket: {wt}/TICKET.md\n\n"
        f"Brief: {brief(arm)}"
    )


def claude_cmd(arm, prompt):
    return [
        "claude", "-p", prompt, "--agent", SYSTEM_AGENT, "--agents", agents_json(arm),
        "--model", CFG["review_model"], "--effort", CFG["review_effort"],
        "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
        "--no-session-persistence", "--permission-mode", "acceptEdits",
        "--settings", json.dumps(SETTINGS),
    ]


def parse_stream(text):
    """The result event of a stream-json transcript (None if absent)."""
    res = None
    for line in (text or "").splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if isinstance(e, dict) and e.get("type") == "result":
            res = e
    return res


def main_model(model_usage):
    if not model_usage:
        return None
    return max(model_usage, key=lambda k: (model_usage[k].get("costUSD") or 0))


class Budget:
    def __init__(self, cap, spent):
        self.cap, self.spent, self.inflight, self.max_seen = cap, spent, 0.0, 0.0
        self.lock = threading.Lock()

    def reserve(self):
        with self.lock:
            est = max(self.max_seen, 3.0)  # conservative per-call estimate until real ones are seen
            if self.spent + self.inflight + est > self.cap:
                return None
            self.inflight += est
            return est

    def settle(self, est, actual):
        with self.lock:
            self.inflight -= est
            self.spent += actual
            self.max_seen = max(self.max_seen, actual)


STOP = threading.Event()  # set by the stop rule: an arm has >25% failed calls after its first 12


def one_call(task, raw, budget, wt_locks, rows_lock, retries_max=1):
    arm, ticket, cond, rep = task["arm"], task["ticket"], task["condition"], task["rep"]
    rid = f"{arm}-{ticket}-{cond}-r{rep}"
    row = {"id": rid, "arm": arm, "ticket": ticket, "condition": cond, "rep": rep,
           "order_in_pair": task["order"], "started_at": None}
    if STOP.is_set():
        row.update(status="skipped_stop_rule", cost_usd=0.0, retries=0)
        return row
    est = budget.reserve()
    if est is None:
        row.update(status="refused_budget", cost_usd=0.0, retries=0)
        return row
    cost, attempt, walls = 0.0, 0, []
    with wt_locks[(ticket, cond)]:
        wt = prep.reset(ticket, cond)
        while True:
            attempt += 1
            row["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            t0 = time.time()
            p = subprocess.run(claude_cmd(arm, prompt_for(arm, ticket, wt)), cwd=wt,
                               capture_output=True, text=True)
            wall = time.time() - t0
            walls.append(round(wall, 2))
            os.makedirs(f"{raw}/claude-json", exist_ok=True)
            open(f"{raw}/claude-json/{rid}-try{attempt}.jsonl", "w").write(p.stdout or "")
            if p.stderr:
                open(f"{raw}/claude-json/{rid}-try{attempt}.stderr", "w").write(p.stderr)
            d = parse_stream(p.stdout)
            open(f"{raw}/claude-json/{rid}-try{attempt}.json", "w").write(json.dumps(d) if d else "")
            ok = bool(d) and p.returncode == 0 and not d.get("is_error") and bool((d.get("result") or "").strip())
            cost += (d or {}).get("total_cost_usd") or 0.0
            if ok or attempt > retries_max:
                break
        # leave the tree as the reviewer left it for post-hoc inspection; reset happens before the next review
        row["worktree_diff_stat_after"] = subprocess.run(
            ["git", "status", "--short"], cwd=wt, capture_output=True, text=True).stdout
    budget.settle(est, cost)
    usage = (d or {}).get("usage", {})
    row.update(
        status="ok" if ok else "failed", exit_code=p.returncode, retries=attempt - 1,
        wall_s=round(sum(walls), 2), wall_attempts_s=walls, cost_usd=round(cost, 6), final_attempt_cost_usd=(d or {}).get("total_cost_usd"),
        model=main_model((d or {}).get("modelUsage")),
        model_ids=sorted(((d or {}).get("modelUsage") or {}).keys()),
        transcript_file=f"claude-json/{rid}-try{attempt}.jsonl",
        usage=usage, model_usage=(d or {}).get("modelUsage"),
        num_turns=(d or {}).get("num_turns"), duration_ms=(d or {}).get("duration_ms"),
        duration_api_ms=(d or {}).get("duration_api_ms"), stop_reason=(d or {}).get("stop_reason"),
        is_error=(d or {}).get("is_error"), permission_denials=(d or {}).get("permission_denials"),
        session_id=(d or {}).get("session_id"), claude_version=subprocess.run(
            ["claude", "--version"], capture_output=True, text=True).stdout.strip(),
        price_table="Claude Code total_cost_usd (CLI price table, list basis); not recomputed",
        review_file=f"reviews/{rid}.md" if ok else None,
    )
    if d and d.get("result"):
        os.makedirs(f"{raw}/reviews", exist_ok=True)
        open(f"{raw}/reviews/{rid}.md", "w").write(d["result"])
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--tickets", nargs="+", required=True)
    ap.add_argument("--conditions", nargs="+", required=True)
    ap.add_argument("--reps", type=int, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=CFG["max_concurrency"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dump-args", help="write each arm's full claude argv (one arg per line) to <dir>/args-<arm>.txt and exit")
    a = ap.parse_args()
    if a.dump_args:
        os.makedirs(a.dump_args, exist_ok=True)
        for arm in ("A", "B"):
            wt = prep.wt_path(a.tickets[0], a.conditions[0])
            with open(f"{a.dump_args}/args-{arm}.txt", "w") as f:
                for x in claude_cmd(arm, prompt_for(arm, a.tickets[0], wt)):
                    f.write(x.replace("\n", "\\n") + "\n")
        return
    raw = os.path.abspath(a.raw)
    os.makedirs(raw, exist_ok=True)
    path = f"{raw}/reviews.jsonl"
    existing = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
    done = {r["id"] for r in existing if r.get("status") == "ok"}
    spent = sum(r.get("cost_usd") or 0 for r in existing)

    rng = random.Random(a.seed)
    tasks = []
    for rep in range(1, a.reps + 1):
        for ticket in a.tickets:
            for cond in a.conditions:
                arms = ["A", "B"]
                rng.shuffle(arms)  # randomized arm order per (input, rep)
                for i, arm in enumerate(arms):
                    tasks.append({"arm": arm, "ticket": ticket, "condition": cond, "rep": rep, "order": i})
    tasks = [t for t in tasks if f"{t['arm']}-{t['ticket']}-{t['condition']}-r{t['rep']}" not in done]
    print(f"tasks={len(tasks)} spent_so_far=${spent:.2f} cap=${CFG['budget_cap_usd']}", flush=True)
    if a.dry_run:
        for t in tasks:
            print(t)
        return
    for t in a.tickets:
        for c in a.conditions:
            prep.ensure(t, c)
    budget = Budget(CFG["budget_cap_usd"], spent)
    wt_locks = {(t, c): threading.Lock() for t in a.tickets for c in a.conditions}
    rows_lock = threading.Lock()
    with cf.ThreadPoolExecutor(max_workers=min(a.concurrency, CFG["max_concurrency"])) as ex:
        futs = [ex.submit(one_call, t, raw, budget, wt_locks, rows_lock) for t in tasks]
        for f in cf.as_completed(futs):
            row = f.result()
            with rows_lock:
                open(path, "a").write(json.dumps(row) + "\n")
            print(f"{row['id']} {row['status']} wall={row.get('wall_s')}s cost=${row.get('cost_usd')}", flush=True)
            with rows_lock:
                rows = existing + [json.loads(l) for l in open(path)]
            for arm in ("A", "B"):
                ran = [r for r in rows if r["arm"] == arm and r["status"] in ("ok", "failed")]
                if len(ran) > 12 and sum(r["status"] == "failed" for r in ran) / len(ran) > 0.25:
                    STOP.set()


if __name__ == "__main__":
    main()
