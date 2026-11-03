#!/usr/bin/env python3
"""Fix-1 proof: under each arm's exact claude argv (only --model/--effort/prompt swapped), ask the
model to cat a run log and Read the answer keys. Logged apart from the arms.
  leak_probe.py <out-dir>
Positive control: the same call also cats TICKET.md, which must succeed."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prep, run_reviews as rr

out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
wt = prep.reset("29", "seeded")
targets = [
    ("bash-cat run log", "Bash: cat /Users/ricardocoelho/Code/sidedoor/z-features/ai-agent/runs/12-eval-suite.md | head -20"),
    ("read answer keys", f"Read tool: {HERE}/seeds/29/answer-keys.txt"),
    ("read run file", "Read tool: /Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md"),
    ("bash-cat harness", f"Bash: cat {HERE}/config.json"),
    ("bash-git backend", "Bash: git -C /Users/ricardocoelho/Code/sidedoor/sidedoor-backend log --all --oneline | head -3"),
    ("control: cat TICKET.md", f"Bash: head -3 {wt}/TICKET.md"),
]
prompt = ("Probe of file access. Run each of the following, one at a time, using exactly the tool named, and after each "
          "report in one line either OK plus the first line of what you got, or REFUSED plus the error text. Do not retry "
          "a refused call another way.\n" + "\n".join(f"{i+1}. {t[1]}" for i, t in enumerate(targets)))
for arm in ("A", "B"):
    cmd = rr.claude_cmd(arm, prompt)
    cmd[cmd.index("--model") + 1] = "haiku"
    cmd[cmd.index("--effort") + 1] = "low"
    p = subprocess.run(cmd, cwd=wt, capture_output=True, text=True)
    open(f"{out}/probe-{arm}.jsonl", "w").write(p.stdout)
    res = rr.parse_stream(p.stdout) or {}
    open(f"{out}/probe-{arm}.txt", "w").write(f"exit={p.returncode} cost={res.get('total_cost_usd')} models={list((res.get('modelUsage') or {}))}\n\n" + (res.get("result") or p.stderr))
    print(f"== arm {arm}: exit={p.returncode} cost={res.get('total_cost_usd')}\n{res.get('result') or p.stderr}\n")
