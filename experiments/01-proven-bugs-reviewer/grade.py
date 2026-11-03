#!/usr/bin/env python3
"""Grading with codex (gpt-6.1-sol, medium, read-only), logged apart from the arms.

  grade.py --raw <dir> [--seed 1] [--sample-size 20]

Reads  <raw>/reviews.jsonl and <raw>/reviews/*.md
Writes <raw>/grader.jsonl            one row per codex call (step, model, wall, tokens, exit)
       <raw>/extracted/<id>.json     step 1: findings {file,line,tag,effect}, proofs stripped
       <raw>/graded/<ticket>-<cond>.json   step 2: shuffled blind grading + id->review map
       <raw>/samples/human-check.md  step 3: blind sample of non-hits (+ human-check-key.json)
Answer keys come from seeds/<ticket>/answer-keys.txt and are only ever put in the grader prompt,
never in a worktree.
"""
import argparse, json, os, random, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prep

CODEX = os.path.expanduser("~/.claude/skills/rc-codex/scripts/codex-run.sh")
MODEL, EFFORT = "gpt-6.1-sol", "medium"
HIT_RULE = ("A finding hits a seed when it names the seed's file, describes the defect's effect, and locates it "
            "by any one of: a line within ±10 of the seed, the enclosing function's name, or a quote of the seeded code.")

EXTRACT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["findings"],
    "properties": {"findings": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["file", "line", "tag", "effect", "quote"],
        "properties": {
            "file": {"type": "string"}, "line": {"type": ["integer", "null"]},
            "tag": {"type": "string", "enum": ["Important", "Nit", "Pre-existing", "Other"]},
            "effect": {"type": "string"}, "quote": {"type": "string"}}}}},
}
GRADE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["grades"],
    "properties": {"grades": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "hit_seed", "verdict", "reason"],
        "properties": {
            "id": {"type": "string"}, "hit_seed": {"type": ["string", "null"]},
            "verdict": {"type": "string", "enum": ["hit", "real-but-unseeded", "false", "unsure"]},
            "reason": {"type": "string"}}}}},
}


def codex(step, label, prompt, cwd, schema, raw):
    d = f"{raw}/codex-work"
    os.makedirs(d, exist_ok=True)
    sp, op, lp = f"{d}/{label}.schema.json", f"{d}/{label}.out.json", f"{d}/{label}.log"
    json.dump(schema, open(sp, "w"))
    env = dict(os.environ, CODEX_LOG=lp)
    t0 = time.time()
    p = subprocess.run([CODEX, "-C", cwd, "-s", "read-only", "-m", MODEL,
                        "-c", f"model_reasoning_effort={EFFORT}", "--skip-git-repo-check",
                        "--output-schema", sp, "-o", op, prompt],
                       capture_output=True, text=True, env=env)
    wall = time.time() - t0
    log = open(lp).read() if os.path.exists(lp) else ""
    tokens = None
    if "tokens used" in log:
        import re
        m = re.search(r"tokens used\s*\n\s*([\d\s,.\u202f\u00a0]+)", log)
        if m:
            tokens = int(re.sub(r"\D", "", m.group(1)))
    row = {"step": step, "label": label, "model": MODEL, "effort": EFFORT, "sandbox": "read-only",
           "exit_code": p.returncode, "wall_s": round(wall, 2), "tokens_used": tokens, "log": lp}
    with open(f"{raw}/grader.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    if p.returncode:
        raise RuntimeError(f"codex {label} failed ({p.returncode}): {p.stderr[-500:]}")
    return json.load(open(op))


KEYS_FILE = None  # --keys override (used only to re-grade an earlier smoke against the keys it ran under)


def load_keys(ticket):
    keys = []
    for line in open(KEYS_FILE or f"{HERE}/seeds/{ticket}/answer-keys.txt"):
        if line.startswith("#") or not line.strip():
            continue
        kind, rest = line.strip().split(" · ", 1)
        keys.append({"id": f"S{len(keys)+1}", "kind": kind, "key": rest})
    return keys


def extract(raw, rows):
    scratch = tempfile.mkdtemp(prefix="exp01-extract-")
    for r in rows:
        if r["status"] != "ok":
            continue
        out = f"{raw}/extracted/{r['id']}.json"
        if os.path.exists(out):
            continue
        text = open(f"{raw}/{r['review_file']}").read()
        prompt = (
            "Extract the findings from the code review below as JSON. One entry per distinct finding: "
            "file (path as written), line (first line number given, or null), tag (the review's own tag: "
            "Important, Nit or Pre-existing; Other if it has none), effect (one or two sentences: what the "
            "defect is and what goes wrong because of it), quote (the shortest snippet of code the finding "
            "quotes from the reviewed code, copied as written, or an empty string when it quotes none; a "
            "command or its output is not a code quote). Strip every proof: no commands, no command "
            "output, no test names, no reproduction steps, no statements about whether it was run or "
            "proven. Do not judge or reword the claim beyond that, do not add findings, do not merge "
            "findings the review lists separately, and skip praise or summary lines.\n\n--- REVIEW ---\n" + text)
        res = codex("extract", f"extract-{r['id']}", prompt, scratch, EXTRACT_SCHEMA, raw)
        os.makedirs(f"{raw}/extracted", exist_ok=True)
        json.dump(res, open(out, "w"), indent=1)


def grade(raw, rows, seed):
    rng = random.Random(seed)
    inputs = sorted({(r["ticket"], r["condition"]) for r in rows if r["status"] == "ok"})
    out_all = {}
    for ticket, cond in inputs:
        gp = f"{raw}/graded/{ticket}-{cond}.json"
        if os.path.exists(gp):
            out_all[(ticket, cond)] = json.load(open(gp))
            continue
        items = []
        for r in rows:
            if r["status"] == "ok" and (r["ticket"], r["condition"]) == (ticket, cond):
                for f in json.load(open(f"{raw}/extracted/{r['id']}.json"))["findings"]:
                    items.append({"review": r["id"], **f})
        rng.shuffle(items)
        for i, it in enumerate(items, 1):
            it["fid"] = f"F{i:02d}"
        keys = load_keys(ticket) if cond == "seeded" else []
        wt = prep.reset(ticket, cond)  # the pristine tree the reviewers saw
        blind = [{k: it[k] for k in ("fid", "file", "line", "tag", "effect", "quote")} for it in items]
        prompt = (
            "You grade code-review findings against answer keys. The working directory is the code the "
            "reviewers saw: the ticket diff is uncommitted (`git diff HEAD`)"
            + (", with planted bugs already in it" if keys else "")
            + ". Read it as needed; do not modify anything.\n\n"
            "ANSWER KEYS (file:line · function · effect):\n"
            + ("\n".join(f"{k['id']}: {k['key']}" for k in keys) or "(none: the code is the clean ticket diff)")
            + f"\n\nHIT RULE, applied exactly: {HIT_RULE}\n\n"
            "For each finding return: hit_seed (the key id it hits, else null), verdict, reason (one sentence). "
            "verdict is 'hit' when the hit rule holds for a key; otherwise read the code the finding "
            "points at and give 'real-but-unseeded' (a genuine defect the diff introduces or exposes), "
            "'false' (the code does not behave as the finding claims, or it is not a defect), or 'unsure'. "
            "Judge from the code, not from how confident the finding sounds. A finding about code the "
            "diff did not introduce is judged on whether the claim is true. Return one grade per finding id.\n\n"
            "FINDINGS:\n" + json.dumps(blind, indent=1))
        res = codex("grade", f"grade-{ticket}-{cond}", prompt, wt, GRADE_SCHEMA, raw)
        got = {g["id"]: g for g in res["grades"]}
        missing = [it["fid"] for it in items if it["fid"] not in got]
        if missing:
            raise RuntimeError(f"grader skipped findings {missing}")
        rec = {"ticket": ticket, "condition": cond, "keys": keys,
               "findings": [{**it, **{k: got[it["fid"]][k] for k in ("hit_seed", "verdict", "reason")}} for it in items]}
        os.makedirs(f"{raw}/graded", exist_ok=True)
        json.dump(rec, open(gp, "w"), indent=1)
        out_all[(ticket, cond)] = rec
    return out_all


def sample(raw, graded, n, seed):
    non_hits = [dict(f, ticket=g["ticket"], condition=g["condition"])
                for g in graded.values() for f in g["findings"] if f["verdict"] != "hit"]
    rng = random.Random(seed + 1)
    above = [f for f in non_hits if f["tag"] == "Important"]
    rest = [f for f in non_hits if f["tag"] != "Important"]
    rng.shuffle(above), rng.shuffle(rest)
    pick = (above + rest)[:n]
    rng.shuffle(pick)
    os.makedirs(f"{raw}/samples", exist_ok=True)
    lines = ["# Human check: label each finding real / false / unsure from the code (blind to arm and to codex's verdict)", ""]
    key = []
    for i, f in enumerate(pick, 1):
        lines += [f"## H{i:02d}  ({f['ticket']} {f['condition']})",
                  f"- where: `{f['file']}:{f['line']}`", f"- tag: {f['tag']}", f"- claim: {f['effect']}", f"- quote: {f.get('quote', '')}",
                  "- your label: ", ""]
        key.append({"hid": f"H{i:02d}", "fid": f["fid"], "review": f["review"], "codex_verdict": f["verdict"]})
    open(f"{raw}/samples/human-check.md", "w").write("\n".join(lines))
    json.dump(key, open(f"{raw}/samples/human-check-key.json", "w"), indent=1)
    return len(pick)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--sample-size", type=int, default=20)
    ap.add_argument("--keys", help="answer-keys file to use instead of seeds/<ticket>/answer-keys.txt")
    a = ap.parse_args()
    global KEYS_FILE
    KEYS_FILE = os.path.abspath(a.keys) if a.keys else None
    raw = os.path.abspath(a.raw)
    rows = [json.loads(l) for l in open(f"{raw}/reviews.jsonl")]
    rows = [r for r in rows if r["status"] == "ok"]
    extract(raw, rows)
    graded = grade(raw, rows, a.seed)
    print("sampled non-hits:", sample(raw, graded, a.sample_size, a.seed))


if __name__ == "__main__":
    main()
