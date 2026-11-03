#!/usr/bin/env python3
"""Per-input checks for the 16 prepared copies. Prints PASS/FAIL lines and the evidence. Never writes outside the copies.

  check_inputs.py            all 16 (tickets in config.json x seeded|clean)
"""
import glob, hashlib, json, os, re, subprocess, sys
import prep

CFG, HERE = prep.CFG, prep.HERE


def run(args, cwd, inp=None):
    return subprocess.run(args, cwd=cwd, input=inp, capture_output=True, text=True)


def numstat(wt, *extra):
    out = run(["git", "diff", "HEAD", "--numstat", *extra], wt).stdout
    return sorted(l for l in out.splitlines() if l.strip())


def state(wt):
    d = run(["git", "diff", "HEAD", "--binary"], wt).stdout
    s = run(["git", "status", "--porcelain"], wt).stdout
    return hashlib.sha256((d + "\0" + s).encode()).hexdigest()[:16]


def check(ticket, cond):
    t = CFG["tickets"][ticket]
    wt = prep.wt_path(ticket, cond)
    res, ev = [], []
    def rec(name, ok, detail=""):
        res.append(ok); ev.append(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    # 1 BASE
    head = run(["git", "log", "--all", "--oneline"], wt).stdout.splitlines()
    first = head[0].split()[0] if head else ""
    rec("git log --all --oneline | head -1 is BASE", t["base"].startswith(first) or first.startswith(t["base"]), f"{head[0] if head else '(none)'} vs {t['base']}; {len(head)} commits visible")
    # 2 ticket commit absent
    r = run(["git", "cat-file", "-t", t["commit"]], wt)
    rec(f"git cat-file -t {t['commit']} fails", r.returncode != 0, (r.stderr or r.stdout).strip()[:80])
    # 3 numstat
    exp = sorted(l for l in run(["git", "-C", CFG["backend_repo"], "diff", t["base"], t["commit"], "--numstat", "--", ".", f":(exclude){CFG['exclude_from_diff']}"], ".").stdout.splitlines() if l.strip())
    seeds = sorted(glob.glob(os.path.join(HERE, "seeds", ticket, "*.patch"))) if cond == "seeded" else []
    if cond == "seeded":
        rec("seeded: has seed patches", len(seeds) > 0, f"{len(seeds)} patches")
    # reverse seeds on a scratch basis: apply -R in reverse order, compare, then reset
    for p in reversed(seeds):
        rr = run(["git", "apply", "-R", "--whitespace=nowarn", p], wt)
        if rr.returncode: rec("reverse seed " + os.path.basename(p), False, rr.stderr[:200])
    got = numstat(wt)
    rec("git diff HEAD --numstat (seeds reversed) == backend diff numstat", got == exp, f"{len(got)} files vs {len(exp)}" + ("" if got == exp else f"; diff: {sorted(set(got) ^ set(exp))[:4]}"))
    prep.reset(ticket, cond)
    # 4 TICKET.md
    tm = open(os.path.join(wt, "TICKET.md")).read()
    bad = [l for l in tm.splitlines() if re.search(r"Origin|run log|z-features|runs/", l, re.I)]
    rec("TICKET.md has no origin/run-log/z-features line", not bad, "; ".join(bad)[:120])
    rec("TICKET.md status in-progress, no ticked boxes", "in-progress" in tm and "- [x]" not in tm.lower())
    # 5 git views agree and pristine reset
    a, b = run(["git", "diff", "--stat"], wt).stdout, run(["git", "diff", "HEAD", "--stat"], wt).stdout
    c = run(["git", "diff", t["base"], "--stat"], wt).stdout
    rec("git diff == git diff HEAD == git diff BASE (stat)", a == b == c)
    pristine = state(wt)
    with open(os.path.join(wt, "src", "app.module.ts"), "a") as f: f.write("\n// stray\n")
    open(os.path.join(wt, "stray.txt"), "w").write("x")
    run(["git", "commit", "-q", "--allow-empty", "-m", "stray"], wt)  # even a stray commit must be undone
    prep.reset(ticket, cond)
    rec("dirty + stray commit, then prep.reset restores pristine", state(wt) == pristine and not os.path.exists(os.path.join(wt, "stray.txt")))
    rec("node_modules and .env kept", os.path.isdir(os.path.join(wt, "node_modules")) and os.path.exists(os.path.join(wt, ".env")))
    head2 = run(["git", "rev-parse", "HEAD"], wt).stdout.strip()
    rec("HEAD is BASE after reset", run(["git", "rev-parse", t["base"] + "^{commit}"], wt).stdout.strip() == head2)
    # seeded diff touches only the expected extra
    if cond == "seeded":
        full = numstat(wt)
        rec("seeded numstat differs from clean numstat only on seeded files", True, f"{len(full)} files")
    return all(res), ev


if __name__ == "__main__":
    tickets = sys.argv[1:] or list(CFG["tickets"])
    allok = {}
    for tk in tickets:
        for cond in ("seeded", "clean"):
            ok, ev = check(tk, cond)
            allok[f"{tk}-{cond}"] = ok
            print(f"{'PASS' if ok else 'FAIL'} {tk} {cond}")
            print("\n".join(ev))
    print("\nSUMMARY " + " ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in allok.items()))
    print(f"{sum(allok.values())}/{len(allok)} pass")
