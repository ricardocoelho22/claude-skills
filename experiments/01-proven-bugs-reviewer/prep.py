#!/usr/bin/env python3
"""Prepare or reset the scratch worktree for one (ticket, condition).

  prep.py <ticket> <seeded|clean>        create (if missing) and reset
  prep.py --reset <ticket> <condition>   reset only (worktree must exist)

Each scratch copy is its own repository (git init + a fetch of BASE only), so it holds history up to
BASE and nothing later: no refs, objects or remotes reach the post-fix commits.

Pristine state: local branch exp-base at BASE; ticket diff (BASE..commit, minus
evals/agent/results) applied uncommitted, new files `git add -N`; for seeded, the seed
patches in seeds/<ticket>/*.patch on top; the ticket file copied in as backend/TICKET.md
(status in-progress, boxes unticked, Outcome section dropped). node_modules and .env kept.
Answer keys never enter the worktree.
"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))


def sh(args, cwd=None, inp=None, check=True):
    r = subprocess.run(args, cwd=cwd, input=inp, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"{args} failed in {cwd}: {r.stderr or r.stdout}")
    return r.stdout


BASE_BRANCH = "exp-base"


def wt_path(ticket, cond):
    return f"{CFG['worktrees_root']}/exp01-{ticket}-{cond}/backend"


def ticket_text(ticket):
    (path,) = glob.glob(os.path.join(CFG["issues_dir"], CFG["tickets"][ticket]["issue_glob"]))
    t = open(path).read()
    t = re.split(r"\n## Outcome", t)[0].rstrip() + "\n"
    t = re.sub(r"(\*\*Status:\*\*)[^\n]*", r"\1 in-progress", t)
    # no line may point at the answers: drop Origin and anything naming a run log or z-features
    t = re.sub(r"[ \t]+Origin:[^\n]*", "", t)  # an inline "Origin: ..." tail on a line
    t = "\n".join(l for l in t.split("\n") if not re.search(r"^\W*Origin\b|\*\*Origin:\*\*|z-features|run log|runs/", l, re.I))
    return re.sub(r"\n{3,}", "\n\n", t).replace("- [x]", "- [ ]")


def ensure(ticket, cond):
    wt = wt_path(ticket, cond)
    if not os.path.isdir(os.path.join(wt, ".git")):
        os.makedirs(wt, exist_ok=True)
        sh(["git", "init", "-q"], cwd=wt)
        full = sh(["git", "rev-parse", CFG["tickets"][ticket]["base"] + "^{commit}"], cwd=CFG["backend_repo"]).strip()
        sh(["git", "fetch", "-q", "--no-tags", CFG["backend_repo"], full], cwd=wt)
        sh(["git", "checkout", "-q", "-B", BASE_BRANCH, "FETCH_HEAD"], cwd=wt)
        sh(["git", "reflog", "expire", "--expire=now", "--all"], cwd=wt)
        sh([CFG["setup_script"], f"exp01-{ticket}-{cond}"])
    return wt


def reset(ticket, cond):
    t = CFG["tickets"][ticket]
    wt = wt_path(ticket, cond)
    base, commit = t["base"], t["commit"]
    sh(["git", "checkout", "-q", "-f", BASE_BRANCH], cwd=wt)
    sh(["git", "reset", "-q", "--hard", base], cwd=wt)
    # -fd without -x keeps ignored files (node_modules, .env, dist)
    sh(["git", "clean", "-fdq"], cwd=wt)
    spec = ["--", ".", f":(exclude){CFG['exclude_from_diff']}"]
    diff = sh(["git", "diff", "--binary", base, commit] + spec, cwd=CFG["backend_repo"])
    sh(["git", "apply", "--whitespace=nowarn", "-"], cwd=wt, inp=diff)
    added = sh(["git", "diff", "--diff-filter=A", "--name-only", base, commit] + spec, cwd=CFG["backend_repo"]).split("\n")
    added = [a for a in added if a]
    if cond == "seeded":
        for p in sorted(glob.glob(os.path.join(HERE, "seeds", ticket, "*.patch"))):
            sh(["git", "apply", "--whitespace=nowarn", p], cwd=wt)
    if added:
        sh(["git", "add", "-N", "--"] + added, cwd=wt)
    open(os.path.join(wt, "TICKET.md"), "w").write(ticket_text(ticket))
    return wt


if __name__ == "__main__":
    a = sys.argv[1:]
    only_reset = False
    if a and a[0] == "--reset":
        only_reset, a = True, a[1:]
    ticket, cond = a
    wt = wt_path(ticket, cond) if only_reset else ensure(ticket, cond)
    print(reset(ticket, cond))
