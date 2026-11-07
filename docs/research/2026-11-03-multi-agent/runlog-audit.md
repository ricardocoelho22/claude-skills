# Run-log audit: how the rc-orchestrate pipeline actually behaves

Date of audit: 2026-11-03. Read-only. Sources: every run file under `z-features/*/runs/` and `z-features/_standalones/*/runs/` (17 files), plus three run files I found outside that scope in `tickets/*/runs/` (same pipeline, included because they hold the oldest evidence). The sibling run dirs (briefs, executor returns), the tickets, `overview.md`, git history of `sidedoor-backend`/`sidedoor-frontend` for diff sizes, git history of `claude-skills` for skill changes, and experiment 01 in `claude-skills/docs/experiments/`.

**Path convention.** Unless absolute, paths are relative to `/Users/ricardocoelho/Code/sidedoor/`. Shorthands: `R12` = `z-features/ai-agent/runs/12-eval-suite.md`, likewise `R13`…`R33`; `RC` = `z-features/_standalones/major-upgrades/runs/clerk-core-3.md`; `RM` = `.../mongoose-9.md`; `RS` = `z-features/_standalones/security-deps/runs/security-deps.md`; `RE` = `tickets/dev-env-guardrails/runs/env-boolean-parsing.md`; `RF` = `tickets/dev-env-guardrails/runs/mongo-fail-fast.md`; `RH` = `tickets/read-endpoint-hardening/runs/read-hardening.md`; `SKILL` = `/Users/ricardocoelho/Code/claude-skills/skills/rc-orchestrate/SKILL.md`. `R12:93` means line 93.

**Epistemic labels.** "Log:" = the run file says it. "Inferred:" = my reading across files, file mtimes or git. The logs do not record wall time or executor/reviewer cost at all; every time figure below is inferred from file mtimes in the run dirs, which can be wrong if files were copied or touched later.

---

## 0. Headline numbers

| | Count | Notes |
|---|---|---|
| Run files read | 20 | 14 ai-agent, 3 `_standalones`, 3 `tickets/`. Plus 1 run dir with no run file (`runs/34-step-date-pill/`, ticket 34 is `done`). |
| Completed (committed) | 17 | In progress / abandoned mid-run: 24, 26, 33 (all started 2026-11-03, live in other sessions). R14's file stops before its commit (commit `af0246c` exists in git). |
| Gate A held | 12 / 20 | ~25 questions. 4 runs where an answer changed scope materially (R15 Q2, R30 Q1, RH D1–D6, R14 Q1/Q2). Most other answers ratified the orchestrator's recommendation. |
| Gate B change requests | ~23 across 6 runs | R14 alone ≈15 over ≥5 rounds. 11 of 17 completed runs had zero. |
| Step-ups (rung) | 7 | R12, R14, R16, R29, RF ×2, RH. |
| Codex failures / fallbacks to Claude | 4 incidents + 1 deliberate route | Usage limit (R14:135, RH:27), silent no-write (RF:80), skill-rename exit 127 (RM:51, not counted). R12 routed Mongo-backed steps to Claude on purpose (R12:92-93). |
| Review-log lines (formal format, R15–R32, 8 runs) | ~78 | ~55 fixed, ~13 rejected, ~9 deferred, 1 routed to trim. Bugs axis: 13 lines across the 8 runs (3 fixed, 7 deferred, 2 rejected-intentional, 1 rejected-wrong — count from experiment 01's run file). |
| `escaped ·` lines logged | **0** | Despite ≥4 qualifying events (§4). |
| `not run` reviewers logged | 0 | Rule added 2026-11-02 (commit b4065ed), after most runs. |
| Retros | 6 / 20 | Logged: R12, RM, R32, RH. Inferred from artifacts: R16 (run dir `retro-*` files), R31 (ticket 32 says "Origin: ticket 31 retro"). Explicitly skipped: R28:94. Unknown for the rest. |
| Live model spend logged | ≈ $7.8 | Evals + throwaway checks only (§2). Executor, reviewer and orchestrator cost: never logged. |

---

## 1. Per-run extraction

Columns 1–8 follow the brief's numbering. "n/a" = the log does not record it.

### R13 — Docs sweep (2026-10-17, docs repo only)
1. Size: 6 files, +170/−31 (R13:41). 0 TDD cycles (docs).
2. Gate A: not held (no mention).
3. Executors: recon codex rung 3; writer codex rung 3 (R13:40-41); fixer codex rung 4 (R13:45). No rejections.
4. Review (old two-axis format, R13:42-44): 5 fixed (wrap lines, contradictory 503/403 rows, missing AGENT_DISABLED, glossary dupes, wording), 5 rejected with reasons. No log format.
5. Gate B: not recorded; "Committed b6e6218 … pushed" (R13:47).
6. Wall: inferred ≈ 1 h (run dir 13:10–13:19, run file 14:18).
7. Retro: n/a.
8. Writer found a spec/code disagreement (spec ~50k replay tokens, code 30k) and documented the code (R13:41); it resurfaced as ticket 24's "30K-vs-spec-50K rationale" item.

### R14 — Write tracer, minimal proposal flow (2026-10-17 → 10-24, backend+frontend+docs)
1. Size: backend `af0246c` 45 files +2925/−275; frontend `a4b706b` 14 files +1114/−7 (git). 4 planned cycles grew to 7 test-first cycles (1–4, A3 fold-in, 5 upgrade-in-place, 6 manual-check fixes) + docs.
2. Gate A held, 3 questions, all material: two slices (free/paid), next-message dismissal of pending proposals, title+description only (R14:30-35, R14:74). Gate A Q1's "tier change → 409" was later reversed at Gate B (R14:173).
3. Executors: all codex at rung 4 for design-heavy cycles 1–3, rung 3 for cycle 4 (R14:79-98). Rejections and repairs: c1b follow-up resume for a Mongo spec that self-skipped in sandbox (R14:83); c3b over-strict Date assertion → fresh codex test fix (R14:93); frontend fixer **blocked** by a brief boundary, resumed with a widened one (R14:111); TTL backend test helper stripped by Mongoose timestamps → **step-up 3→4** (R14:124); **codex usage limit** → trim on Claude sonnet (R14:135); design work on a Claude "designer" agent at Ricardo's request (R14:139-147); A3 cycle on Claude (codex limited) (R14:150-152); cycle 6 needed 3 test-only re-runs because the test-writer missed an assertion and fought a shared next-intl mock (R14:202-204). Orchestrator hand-reverted Prettier churn and wrote a CLAUDE.md rule itself (R14:165-166) — executor work by the orchestrator.
4. Review (old format): 12 backend + 6 frontend fix-now items incl. real design fixes (B10 one-proposal-per-turn made atomic via unique partial index, B11 per-field update instead of whole-array replace) (R14:103-104); 1 deferred (crash between claim and apply) (R14:106). Round-1b TTL review found an approve/expiry race (R14:131). Round-4 spec reviewer found that existing conversations of paid users would 409 (R14:170) → product decision. A3 spec review found a parked card stuck after abort (R14:155). Backend fixer itself introduced a defect (click-dismissed proposals older than 24 h reload as expired) caught by orchestrator (R14:174).
5. Gate B: ≥5 rounds, ≈15 requests: TTL 24 h (product; plan gap) (R14:122); "run the TTL change through the full cycle" (process enforcement) (R14:128); "UI a bit bland" (R14:137); card width, placement, three prototype variants, tense-aware labels, footer variant (UX) (R14:141-146); "run the fold-in through the orchestrate flow" (process) (R14:148); round 4 code read: three refactors, AgentService split (→ ticket 25), drop an unused in-memory copy, prompt rewrite per writing-for-agents that "fixes 'do not re-propose' vs message-dismiss conflict" (a real prompt bug), CLAUDE.md rule (R14:163); upgrade-in-place decision (R14:173); then "fix both manual findings; also remove the dev rollover override" (R14:195). No round triggered the "ask whether the approach needs rethinking before a fourth round" rule (that rule postdates this run).
6. Wall: inferred. Phase 0→trim 10-17 13:12–15:12 (2 h). Then Gate B: 15:30–17:53 on 10-17, a **7-day gap**, 10-24 18:51–20:31. 45 of 77 run-dir artifacts (58%) were produced after the first Gate B. Live spend ≈ $1.01 (R14:99, :169, :182).
7. Retro: not recorded. Lessons visible in-run: CLAUDE.md "Model-Facing Text" rule (R14:166). The writing-for-agents request recurred in R15 and R31 before it became a skill rule (§3).
8. **Human-only catches:** TTL/staleness gap; the prompt's re-propose/dismiss conflict; the AgentService size. **Browser checks by the orchestrator** (R14:190-194) found 2 bugs no reviewer or test had: the admin capability list showed the raw key `journey_write`, and an expired proposal's tool output said `dismissed`, so the model told the user "was dismissed". **Orchestrator's own call:** with 3 unanswered asks, it chose to reveal the card at turn end, flagged reversible (R14:146).

### R12 — Eval suite, v0 launch gate (2026-10-24 → 10-31, backend)
1. Size: `a08abf1` 102 files +8838/−204, most of it committed eval transcripts (R12:153). 4 cycles (cycle 4 content-only, no tests).
2. Gate A held: 2 questions + 1 derived rule (R12:45-50). Q1 picked the Spanish seed user and two new seed journeys (moderate). Q2 approved a $3.50 spend envelope.
3. Executors: c1b codex returned 7/7 red (couldn't run Mongo in sandbox; real cause a seed template defaulting to `draft`) → **step-up 3→4 and route switch to Claude** (R12:91-94). Cycles 3 and the fixer ran on Claude because their specs are Mongo-backed (R12:105, :123). No codex failures.
4. Review (old format, 2 axes): 9 fix items incl. "rollover case never asserted it rolled" (R12:117); 3 rejected incl. "annotate every local" (repo idiom) (R12:118) — the same rule later runs fixed (§3); 1 deferred to Gate B → became ticket 29.
5. Gate B: round 1 three requests (fixture data, assertion widening, Language prompt paragraph) (R12:137-140); round 2 "commit with the gate red, create tickets" → tickets 26–29 (R12:146-148).
6. Wall: inferred. Phase 0→Gate B 10-24 20:32–22:00 (1.5 h); commit 10-31 (7 days later). Live spend $0.92 of $3.50 (R12:149). One full eval: $0.45, 2 min 33 s (R12:128).
7. Retro: user took 1 item ("Prettier in checkup"), which turned into a deferred ticket (447 files); not taken: verify codex network access, slice→ticket lines in overview.md, foreground suite logging (R12:157). The not-taken overview/feature-page item recurred 3 more times (§3).
8. **Live eval caught what tests did not:** an assertion false positive ("I'm not ChatGPT" echoes the user) (R12:113), a text-join bug in the driver (R12:114), a fixture contradiction with seeded data (R12:130), an assertion gap (R12:131), and real prompt failures (Sonnet keeps Spanish) (R12:129). **The prompt fix was judged on n=1:** "Prompt fix partially effective: next-step-follow-up (paid) now passes" (R12:143). Later evidence contradicts that read: R29's A/B gave the HEAD prompt 6/8 and the candidate 4/11, "inconclusive" (R29:160); R26's N=5 baseline (after R12's fix) shows `next-step-follow-up` 0/5 failures but `empty-timeline-english` 3/5 (R26:61). The suite was committed red as the "baseline" (R12:147).

### RS — Security deps (2026-10-24 → 10-26, 3 repos)
1. Size: backend `6b0b288` 4 files +3516/−5140 (lockfiles); frontend `e54f016` 2 files. 3 impl-only cycles (no test-writer: "dependency bumps add no behavior") (RS:23).
2. Gate A: not held.
3. Executors: 3 codex implementers in parallel (RS:57-59). F's lint broke because the plan bumped `eslint-config-next` without an advisory → orchestrator reverted, "the plan item was wrong" (RS:68). B: two in-range drifts rejected as plan issues (duplicate mongodb driver; stripe needing a `@ts-expect-error`) (RS:74-76). `codex resume --last` dropped network flags (RS:83).
4. Review (2 axes): 1 fix (docs version), 1 user call (CLAUDE.md edits), several handled/accepted (RS:90-97).
5. Gate B: approved; follow-up request to clear moderates (RS:113) and to write the major-upgrade tickets (RS:116).
6. Wall: n/a; inferred 10-24 22:06 → 10-26.
7. Retro: n/a. The resume-flag note (RS:83) was not turned into a skill change until 11-02 (`ccb4ab0`), after it bit again in RM.
8. Orchestrator's plan errors caused all three rejections; the executor followed the brief each time.

### RC — Clerk Core 3 (2026-10-27 → 10-31)
1. Size: backend 4 files +61/−87, frontend 3 files +181/−218 (git). 2 impl-only cycles.
2. Gate A: not held; explorer skipped (RC:22).
3. Executors: codex rung 2 ×2, fixer rung 4. No rejections. The `@clerk/upgrade` CLI never ran: sandbox EPERM, then the unsandboxed run was denied by the permission classifier (RC:55, :87).
4. Review: 4 fixes incl. a real one, both reviewers: building the Request outside `try` turned a malformed host into 500 instead of 401 (RC:59).
5. Gate B: shown 10-27, approved 10-31 after the user ran signed-in checks (RC:81).
6. Wall: inferred execution 10:59–11:17 (18 min); 4 days to approval.
7. Retro: n/a.
8. Orchestrator's server-side checks found a deprecation (`createRouteMatcher`) → follow-up ticket 04 (RC:80, :86). A real signed-in token check was impossible for the agent (classifier) (RC:79); only the human covered it.

### RM — Mongoose 9 (2026-10-27 → 10-31)
1. Size: `8502108` 39 files +126/−182. 1 impl-only cycle.
2. Gate A: not held; "Decisions (orchestrator)" (RM:18-22). Two mid-run escalations instead.
3. Executors: codex rung 3. Return "rejected-pending-decision": typecheck caught a silently dropped field in fixtures; 64 Mongo suites failed on a driver ESM dynamic import under Jest (orchestrator diagnosis) → user (RM:46-48). Resume exited 127 because skills were renamed mid-pause (RM:51). Implementer-2's green suite had self-skipped Mongo (resume dropped the network flag) (RM:52).
4. Review: 0 findings on both axes (RM:55).
5. Gate B: shown 10-31; user asked "what insurances of no regressions" (RM:67) → smoke tests plus coverage: 14 of 58 changed `returnDocument` sites sit in methods no test calls (RM:71).
6. Wall: inferred first segment 10:59–11:12 (13 min); 4-day wait for the user's decision.
7. Retro: user took 1 of 5 items (re-pass network flag on resume → `ccb4ab0`). Not taken: probe `cd <repo>`, a Mongo-skip guard ticket, **full-suite check before offering escalation options**, branch from origin (RM:75). The `cd <repo>` item recurred in R32 and R33 (§3).
8. **Orchestrator decision that mattered:** option A (NODE_OPTIONS flag) was offered after checking only "both organization specs 148/148" (RM:49). The full suite then failed on nanoid ESM (RM:56) → second escalation. The retro item that would have prevented this was not taken.

### RE — Env boolean parsing (2026-10-24, backend)
1. Size: n/a; 1 cycle, 16 tests.
2. Gate A: not held.
3. Executors: codex rung 2 ×2, fixer rung 4, trimmer rung 3. No rejections (RE:50-71).
4. Review: 3 fixes (return type, Prettier, redundant `.optional()`), 2 rejected (RE:56-58).
5. Gate B: approved, merged (RE:74-76).
6–7. n/a.
8. The ticket itself came from a human-observed bug in RH's browser checks (RH:119).

### RF — Mongo fail-fast (2026-10-24, backend+docs)
1. Size: n/a; 1 cycle.
2. Gate A held: 1 decision (constant 10 s timeout, no retries, with accepted trade-offs) (RF:23).
3. Executors: 1b skipped typecheck → **step-up 3→4** (RF:59-61). Manual-checks executor (codex luna low) "claimed the file but nothing was written (exit 0)" → **step-up to Claude haiku** (RF:80).
4. Review: Spec 0; Standards 4 fix, 1 trim, 2 rejected — incl. "explicit types on inferred locals: matches repo practice" (RF:74).
5. Gate B: user asked for manual checks after Gate B; orchestrator ran them (RF:84-87).
6–7. n/a.
8. Post-merge full suite found 4 load-flaky suites (RF:92-93), a list every later run carries.

### RH — Read-endpoint hardening, T01 only (2026-10-17 → 10-24, 3 repos)
1. Size: n/a; T01 2 cycles. A 4-ticket run; only T01 shipped, T02–T04 released (RH:137-140).
2. Gate A held: 6 decisions D1–D6, all material (403 vs 404 policy, team scope, public projection shapes with two new routes, connections scope, test seams, search fields) (RH:29-46).
3. Executors: whole run on Claude after codex usage limit on the first real call (RH:6, :27). C2a test-writer rejected on typecheck → **step-up 3→4** (RH:99-100).
4. Review: 4 fix, 1 trim, 5 rejected (RH:102-106).
5. Gate B: 1 request (refactor a guard's threaded flag) (RH:112).
6. Wall: inferred one week (10-17 → 10-24). The run file was lost with the session scratchpad and **rebuilt by replaying the transcript** (RH:109-110).
7. Retro applied: run file lives beside the ticket; `worktrees/setup.sh`; two tickets (RE, RF) (RH:131-135). Seen applied: every later run uses setup.sh and keeps the run file in the repo tree.
8. Browser checks found a pre-existing bug (`z.coerce.boolean` makes "false" true; 429s during checks) (RH:119) → RE.

### R25 — Split AgentConversationService (2026-10-31 → 11-01, backend+docs)
1. Size: backend `bead2cb..3e70bff` +972/−781 (experiment 01 table). 1 impl cycle (no 1a: pure move) + docs.
2. Gate A held: names (Q1) and controller injection (Q2) (R25:66-67). Naming mostly.
3. Executors: codex rung 3, fixer rung 4, Gate B fixer rung 2 → rung 4. No rejections. Orchestrator verified "pure move" with a body-equivalence script over 29 methods (R25:72) — the strongest self-verification in the corpus.
4. Review: standards 2 fixed, 1 rejected-intentional, 2 deferred pre-existing; spec 1 fixed, 1 rejected; bugs 0 findings (R25:116-124).
5. Gate B: 1 request ("remove some of the nesting") (R25:92), round review 2 Nits fixed.
6. Wall: inferred 15 min of execution on 11-01 13:08–13:23; whole run 10-31 18:08 → 11-01 16:19, gated by a merge queue run by another session (sidedoor-39) (R25:89-90).
7. Retro: n/a.
8. Origin: Ricardo's code read at R14's Gate B (ticket 25, "Origin").

### R28 — Eval language check for short replies (2026-10-31 → 11-01, backend)
1. Size: +127/−5 (experiment table). 1 cycle.
2. Gate A: not held; orchestrator design with a deliberate deviation from the ticket ("paso" excluded) (R28:33), confirmed at Gate B.
3. Executors: codex rung 3 ×2, fixer rung 4, trimmer rung 3. None rejected (R28:94).
4. Review: 7 lines — 5 fixed (incl. Important: accented proper nouns score as Spanish), 1 to trim, 1 rejected-intentional (R28:72-78).
5. Gate B: approved, no changes (R28:89).
6. Wall: inferred execution 18:07–18:27 (20 min); merge next day, ordered after other sessions.
7. Retro: "not run (not in Ricardo's approval)" (R28:94).
8. Orchestrator built an offline re-grade tool to prove "only the fix changes grades" (R28:22, :67) — good practice. It ran the smoke eval at the user's request (R28:85).

### R29 — Seed coverage: contacts, invitations, microsite (2026-10-31 → 11-02, backend+docs)
1. Size: +608/−25 (experiment table). 2 planned cycles + cycle 3 (search) + prompt fix.
2. Gate A: not held.
3. Executors: 1b red from a **plan error (mine)**: pinned role 'Home Stager', service derives it (R29:89); prompt fix rung 1 left a stray "Use" → **step-up 1→2** (R29:142). Codex ran Mongo specs in-sandbox with `network_access=true` (R29:87).
4. Review: 10 lines (8 fixed incl. Important `deletedAt: null` vs `$exists:false`, and Important "husband/wife" substring check that fails compliant replies) (R29:115-124); fix-round review 6 lines (R29:148-153).
5. Gate B: approved, "decisions taken as recommended" (R29:164).
6. Wall: inferred execution 18:07–18:37 (30 min) on 10-31; then a day of manual-check queueing, rebases over 28, 25 and 15, and evals.
7. Retro: n/a.
8. **Browser checks by the orchestrator found 2 bugs** that reviewers, specs and (not-yet-run) evals had not: the model offered "e.g., spouse, co-buyer" (breaks the never-infer rule), and contact search could not match a full name (R29:131). Fixed in-ticket "outside original ticket scope" (R29:135). Nikki/Luis UI checks were never run (R29:175). Final eval: 3 unrelated fails/flakes accepted (R29:159); A/B inconclusive at n=11 vs 8 (R29:160).

### R15 — Full ops union, atomic batch (2026-10-31 → 11-01, 3 repos)
1. Size: backend +2968/−296 (+932/−233 non-test) (experiment table); frontend `bc7a3df` +506/−32. 6 cycles (4 test-first; cycle 2 split in two mid-run, R15:102).
2. Gate A held: Q1 nested steps; **Q2 precedents/resources out → ticket 30** (R15:41, :46, :94). Material scope split.
3. Executors: all codex, rung 4 for design-heavy. No rejections. Prompt text took 4 rounds driven by the orchestrator and live checks (R15:117-122).
4. Review log (first run in the new format): 12 lines, 9 fixed, 3 deferred (R15:152-164). One Important spec bug (preview TypeError when a section is created then removed in one batch) (R15:156). The orchestrator's verification missed a stray "Remove a" in the prompt: "I read only the +/- lines" (R15:154). Bugs Important (per-step milestone events) deferred to ticket 16 with an acceptance line added (R15:162) — a clean handoff.
5. Gate B: 2 requests: writing-for-agents on the prompt (text quality), refactor journeys.service (code quality) (R15:180-181). Change 1 **regressed** Haiku status handling (1/3), caught by the live check, fixed as change 1b (R15:182).
6. Wall: inferred. Phase 0 10-31 18:15–18:20; Gate A overnight; execution 11-01 13:09–13:57 (48 min); Gate B changes 15:55–16:05. Live spend ≈ $0.90 + $0.75 (R15:138, :184).
7. Retro: n/a.
8. **Escaped to post-merge human testing (→ ticket 31):** a large add-section proposal hits the 2,000-token paid cap; turns go silent or prose-only; the card's step list renders as bare lines (ticket 31 lines 3-21). The 10 manual checks passed (R15:189). The live check's largest add_section had 2 steps (`runs/15-full-ops-union/live-check-brief.md:17`), and its brief never sets `maxOutputTokens` (inferred: the throwaway script did not run at the production cap). Also escaped: R15 changed the paid prompt so deletions become proposals, which left eval case `delete-step-refusal` stale until R32 noticed (`z-features/_standalones/eval-guardrails/SPEC.md:9`). Browser checks found a pre-existing "skipped step renders as locked" bug (R15:190); I found no ticket for it.

### R30 — Step precedents + resources ops (2026-11-02, 3 repos)
1. Size: backend +924/−38 (experiment table); frontend `7e2701d` +149/−5. 5 cycles (3 test-first).
2. Gate A held: **Q1 resources dropped entirely ("we want to delete them anyway")**; Q2 reject cycles (R30:36-38). Scope halved.
3. Executors: all codex, no rejections.
4. Review: 10 lines, 6 fixed, 4 rejected-intentional (R30:135-144). Bugs Minor upgraded to fix-now: stale precedent ids dead-end the model (R30:135).
5. Gate B: approved, no changes (R30:148).
6. Wall: inferred Phase 0→trim 12:52–13:25 (33 min). Live spend $0.39 (R30:113).
7. Retro: n/a.
8. Two pre-existing bugs ticketed (`tickets/dead-step-precedent-ids.md`, `tickets/step-precedent-validation-rest.md`). Haiku invented a step id → deferred because Haiku has no write tools in production (R30:113).

### R31 — Large proposals cut off, section-card steps (2026-11-02, 3 repos)
1. Size: backend +289/−19 (experiment table); frontend `c616b50` 12 files +209/−22. 5 cycles + 1c.
2. Gate A held: cap 6,000 (the orchestrator's suggestion), card shows title + due date (R31:88).
3. Executors: 1b left reds "correctly within its boundary" because the test side never added fixture literals → new cycle 1c (R31:94-95); **1c projection whitelist was a plan gap** found while briefing cycle 2 (R31:56). Prompt took 2 rounds driven by live checks (R31:116-118).
4. Review: 8 lines, 5 fixed, 1 deferred (silent turn on step/budget stop → ticket 33), 2 rejected (one "rejected: wrong" after a $0.018 real-model probe) (R31:145-152).
5. Gate B: approved after one question, "did you use /writing-for-agents" (R31:136).
6. Wall: inferred 10:24–11:47 (1 h 23 m) end to end, the fastest full run. Live spend ≈ $0.56.
7. Retro (inferred): produced ticket 32 ("Origin: ticket 31 retro", ticket 32) and probably `1bdaad6` (writing-for-agents in executors and Standards, committed 11:45 that day).
8. **Rework within a day:** Ricardo found the due-date chip "not pretty" → ticket 34 prototype + rework (ticket 34 lines 3-5). The spec reviewer had flagged "chip butts against title" and the fix only added a margin (R31:150).

### R16 — Batch homeowner notification (2026-11-02, 3 repos)
1. Size: backend +642/−42 (experiment table); frontend `9f2420b` +83. 4 cycles (3 test-first).
2. Gate A held: 2 questions (celebrations per section; exclude the approving pro) (R16:77).
3. Executors: c3a test-writer red **for a fixture reason** (wrong i18n namespace) that the orchestrator's verification missed (R16:101) → **step-up 2→3** (R16:102). Planned routing change dropped: tests green before production (R16:99).
4. Review: 6 lines, 4 fixed, 2 rejected-intentional. One rejection was the orchestrator's own plan call, "every approved batch sends one", which made field-only batches notify the homeowner (R16:113). Flagged at Gate B; kept (R16:137).
5. Gate B: approved, "commit" (R16:132).
6. Wall: inferred 12:55–13:31 for Phase 0→trim (36 min).
7. Retro: not in run file; run dir holds `retro-backend-brief.md` / `retro-frontend-brief.md` (2026-11-02 18:00): a trustworthy notification-coverage check gated in checkup, and a shared real-translator test helper to stop fixture-reason reds (`runs/16-batch-notification/retro-frontend-brief.md:7`). The same day, `b4065ed` added "Intent needs a source" to the skill (SKILL:203) — exactly R16's self-justified rejection.
8. Orchestrator's plan decision changed product behavior and was rubber-stamped by "rejected: intentional" on its own plan, which the rule now forbids.

### R32 — Journey-write eval cases (2026-11-02, backend)
1. Size: +345/−43 (experiment table). 3 cycles (1 test-first).
2. Gate A held: 1 question (make `delete-step-refusal` free-only: it contradicted shipped paid behavior from R15) (R32:68-69).
3. Executors: codex, no rejections, no step-ups (R32:128).
4. Review: 10 lines, 9 fixed, 1 rejected. Bugs Minor: a rejected retry re-anchors `textAfterProposal` → false pass (R32:112).
5. Gate B: 1 request ("raise" cap 3,000 → 4,000) (R32:120).
6. Wall: inferred 12:50–13:20 Phase 0→checkup; Gate B ~1 h later. Live spend $1.23 for two full evals (R32:89, :99).
7. Retro applied (R32:133): feature-page status patch, codex probe `cd <repo>`, eval-guardrails standalone (freshness check; stale results), pnpm worktree gotchas. Commit `b4065ed`.
8. Recon found the cross-ticket contradiction R15 left behind (R32:29).

### R24, R26, R33 — in progress (2026-11-03)
- R24 docs close-out: Gate A skipped, codex writer landed 5 pages +212/−23 (R24:44-46); no review yet.
- R26 paid-tier language mirroring: Gate A Q1 approved N=5 repeat measurement, $4 envelope (R26:40). The baseline at BASE: Sonnet-only, `empty-timeline-english` 3/5 and `english-overrides-spanish-locale` 2/5 first-attempt failures, others 0/5 ($0.71) (R26:61). **First run that measures prompt changes with repetitions.**
- R33 silent turn on step/budget stop: Gate A 2 questions (R33:33-39); codex explorer launched from a non-repo folder failed, "my error" (R33:22).
- Run 34 (date pill): no run file at all; run dir holds only `c1-tests.md` and `c1-impl.md`. Ticket 34 is `done`.

---

## 2. Where time and money go

**What the logs record.** Only live model spend, and only for evals and throwaway prompt checks. Total ≈ $7.8: R12 $0.92, R14 ≈ $1.01, R15 ≈ $1.65, R26 $0.71 so far, R28 $0.04, R29 ≈ $0.57 (plus one aborted full run, uncosted, R29:154), R30 $0.39, R31 ≈ $0.56, R32 $1.23. **Executor (codex) cost, reviewer cost, orchestrator cost and wall time are not recorded anywhere.** Two codex usage-limit hits (R14:135, RH:27) are the only hint of executor consumption.

**External anchor (claude-skills experiment 01).** One Bugs-axis `rc-reviewer` review (opus · medium) cost $6.18 / 16 ≈ $0.39 and took 46 s median (`/Users/ricardocoelho/Code/claude-skills/docs/experiments/01-proven-bugs-reviewer-results.md:60-61`). Inferred: one three-axis review round ≈ $1.2, so on most tickets review alone costs about as much as all logged live spend, and the Opus orchestrator session is likely the largest line item. That cannot be checked from the logs.

**Wall time (inferred from mtimes).** The autonomous segment, Phase 0 through trim, is short and steady: 13–50 min for most tickets (RC 18 min, RM 13 min, R28 20 min, R29 30 min, R30 33 min, R16 36 min, R15 48 min, R31 ~51 min), 1.5–2 h for the large ones (R12, R14). End-to-end elapsed runs from 1.5 h (R31) to a week (R12, R14, RH), and the gap is always a human gate or coordination:
- Gate A spanning a night (R15, R25);
- Gate B or decision waits of 4–7 days (R12, R14, RC, RM);
- merge-order and manual-check queues run by a coordinating session ("Queue: 29 → 25 → 15", R15:168, R25:90), Clerk sign-ins only the human can do (R25:91, R29:132, R29:175), and shared Mongo/ports.

**Phase that dominates.** By elapsed time: Gate B and post-Gate-B coordination, by a wide margin. By executor work: Gate B in one outlier (R14: 58% of artifacts after the first Gate B). By recorded money: live checks/evals (but that is only the money that is recorded).

**Methodology gap (for your critique).** "Where does the money go" cannot be answered from these logs: no per-call token count, no session cost, no timestamps per landing-log line. The rc-codex wrapper prints usage, but the runs don't capture it.

---

## 3. Recurring failure modes, and whether the retro loop fixed them

| Failure mode | Occurrences (evidence) | Retro / fix | Status |
|---|---|---|---|
| Mongo-backed specs self-skip in the codex sandbox and read as green | Risk line in nearly every backend run (R12:74, R14:66, R15:86, R16:65, R25:59, R29:73, R30:76, R31:79, R32:63, R33:63); incidents R12:91, R14:83, RM:52, `runs/12-eval-suite/gateb-1.md:23` | RM retro declined a "Mongo-skip guard ticket" (RM:75). R29 found `network_access=true` works (R29:87). Resume flag fixed in `ccb4ab0`. | Mitigated by the orchestrator re-running every spec itself. Structural guard never built. |
| Codex resume drops `-c` flags | RS:83 (10-24), RM:52 (10-31) | `ccb4ab0` (11-02), after the 2nd occurrence | Fixed |
| Codex must run from a git repo root | RM:6, R32:8, R33:22 | Not taken at RM:75; taken after R32 (`b4065ed`) | Fixed for the probe; R33's explorer still hit it on 11-03 (orchestrator error) |
| Feature-page refresh build loses slice→ticket mapping | R12:88, R25:112, R29:168, R32:130 | Not taken at R12:157; fixed after R32 (`patch-status.py`, `b4065ed`) | Fixed after the 4th occurrence |
| Prettier/format churn in executor diffs | R14:94, R14:103 (B1), R14:165, R25:73/123, R30:91/137, R32:78, RE:56; orchestrator hand-formatted (R12:125) | R12 retro → `tickets/backend-prettier-baseline.md`, still ready-for-agent (447 files) | **Recurring** |
| Untyped locals / missing return types vs CODING_STANDARDS ("Type all … variables", `CODING_STANDARDS.md:11`) | Fix-now in R14:103-104, R14:155, R15:159-160, R29:117, R29:148, R30:139, R32:109, RH:105, RE:56; **rejected** as "repo idiom" in R12:118 and RF:74 | None. rc-tdd/rc-fixer never mention CODING_STANDARDS; typing language appears in 10 of 122 briefs, 9 of them fix briefs written after the review | **Recurring, and triaged inconsistently** |
| User asks for writing-for-agents on model-facing text at Gate B | R14:163, R15:180, R31:136 | `1bdaad6` (11-02) | Fixed after the 3rd occurrence |
| Throwaway live checks rebuilt from scratch each run ("script is gone, so rebuild it") | `runs/14-write-tracer/live-check-brief.md:11`, R15, R30, R31 | R31 retro → ticket 32 (eval cases) | Fixed |
| Test-writer reds for fixture/mock reasons, missed by the orchestrator's verification | R14:93, R14:124, R14:202-204, R16:101 | R16 retro → shared real-translator test helper | Partly fixed (frontend notifications only) |
| Orchestrator plan errors surfacing as executor "failures" | RS:68, RS:74-76, R12:91, R16:99, R29:89, R31:56, RM:49/56 | Not addressed by any retro | **Recurring.** The most common cause of rework in the logs. |
| Load flakiness from 3–4 parallel sessions corrupting BASE-failure capture | R15:29, R25:21-23, R28:20, R29:28, R31:27, R33:26, RF:92-93 | Tickets `frontend-test-teardown-flakes.md`, `dev-env-guardrails/04-flaky-backend-tests.md` | Open |
| Prompt changes judged on one eval run | R12:143, R29:160 (n=11 vs 8, "inconclusive") | R26 now uses N=5 (R26:40, :61) | Being fixed in R26 |

**The retro loop's effectiveness.** Retros ran in about 6 of 20 runs, and the user typically takes one item of several (R12:157, RM:75). Items that were declined came back (feature page, `cd <repo>`, full-suite check before escalation), and were fixed only after 2–4 occurrences. The skill's claim that the retro "reads this log to tune the reviewer briefs" (SKILL:201) has no trace in any run file: no reviewer brief change cites a review log. The one reviewer-brief question that was tested (experiment 01) came from outside the retro loop.

---

## 4. Bugs that escaped, how they were found, and which step should have caught them

No run logged an `escaped ·` line (grep across all 20 files: 0). These events qualify under SKILL:253 or its spirit:

| Escaped defect | Found by | Should have caught it |
|---|---|---|
| R15: large add_section proposal exceeds the 2,000-token paid cap → silent or prose-only turns; card step list renders as bare lines | Ricardo testing after merge (ticket 31 "Origin", lines 3-13) | Plan/live check: cases were tiny (2 nested steps) and the throwaway harness didn't apply the production cap (inferred from the brief). Manual checks passed 10/10 (R15:189). |
| R15: paid prompt turns deletions into proposals; eval case `delete-step-refusal` (R12) still expects a refusal | R32's recon (R32:29) | R15 never ran the eval suite; no rule required it. Now `eval-guardrails` 01. |
| R14: prompt said "do not re-propose" while the design said a new message dismisses the proposal | Ricardo's code read, Gate B round 4 (R14:163) | Spec reviewer (prompt vs Gate A Q2). Not logged as escaped. |
| R14: model told users an expired proposal "was dismissed"; admin page showed raw `journey_write` | Orchestrator's browser checks (R14:194) | Bugs/Spec review; tests didn't cover the replayed tool status or the label catalogue. |
| R29: model offers "spouse, co-buyer"; contact search can't match a full name | Orchestrator's browser checks (R29:131) | The live eval would have caught "spouse" (global avoid-list) but ran after the browser checks; search was pre-existing. |
| R31: date chip styling | Ricardo after merge (ticket 34) | Taste; the spec reviewer half-saw it (R31:150). |
| R12: prompt "fix" credited with fixing `next-step-follow-up` on n=1 | R29 A/B (R29:160), R26 baseline (R26:61) | The measurement design (single run, no baseline). |
| RH: `RATE_LIMIT_ENABLED="false"` enables limiting (pre-existing) | Browser checks (RH:119) | Pre-existing; ticketed as RE. |
| R15: skipped step renders as locked (pre-existing) | Browser checks (R15:190) | Pre-existing. I found no ticket for it. |

**Experiment 01 calls reviewer recall into question.** Its seeds included the 3 real bugs that past Bugs/Standards reviewers had caught (R29 `deletedAt`, R29 slug abort, R32 retry re-anchor). In the experiment, both reviewer arms found 0 of 3 (`.../01-proven-bugs-reviewer-results.md:6`, `:54`). The authors attribute it to variance ("the same arm hit a seed once and missed it the next time", `:81`). Inferred: a single review pass per ticket is a noisy detector, and the run logs' "fixed" counts overstate what a review reliably finds.

---

## 5. What the human catches at Gate A/B

**Gate A (12 runs held, ~25 questions).** Scope and product decisions dominate: two-slice tiering, dismissal semantics, TTL-free design (R14); scope split to a new ticket (R15 Q2); dropping resources outright (R30 Q1); 403-vs-404 policy and public projection shapes (RH D1–D6). In about half the questions the user picked the orchestrator's recommended option ("yes, 6,000" R31:42; "ok to option a" R32:69; "option (b)" R33:33; "yes" R26:40). One Gate A answer was reversed later because its consequence wasn't surfaced (R14 Q1 → upgrade-in-place, R14:173), and a reviewer found it, not the plan.

**Gate B (≈23 requests in 6 runs; 11 of 17 completed runs had none).** By type:
- Code structure / refactor: 6 (R14 round 4 ×3 + AgentService split, R15 #2, R25 nesting, RH guard). Reviewers had flagged some smells; the human asked for more than review found.
- Model-facing text quality: 3 (R12 Language paragraph, R14 prompt rewrite, R15 #1). One of them carried a real behavior bug (R14).
- UX / visual taste: ~5 (R14 rounds 2–3, R32 cap raise; plus ticket 34 after merge).
- Product behavior: 3 (R14 TTL, upgrade-in-place, dev override).
- Process enforcement: 3 (R14 "full-cycle catch-up" for the TTL change, R14 "run the fold-in through the orchestrate flow", RM "what insurances of no regressions").
- Eval fixture/assertion fixes: 2 (R12 round 1).

**Which of these should a reviewer or the plan have caught?** The process-enforcement requests mean the orchestrator tried to skip its own flow (one-shot designer, unreviewed change) until the human objected (R14:128, :148). The prompt conflict (R14) was a review miss. The writing-for-agents requests were a skill gap, now closed. Refactors and UX are legitimately human taste and are the bulk of Gate B time.

---

## 6. Runtime and manual verification vs tests

The skill tells the orchestrator to treat manual checks as a guide and "assume its checks done … verified by the tests and typecheck alone" (SKILL:215). The logs contradict that stance. In the runs where someone actually ran the app, browser, real model or live eval, those runs found most of the defects that tests and reviewers missed:
- Browser/app checks: R14 (2 bugs), R29 (2 bugs), RH (1 pre-existing bug), R15 (1 pre-existing), RC (1 deprecation), RF (boot behavior confirmed), RM (smoke + coverage gap).
- Real-model checks: R14 (2 prompt fixes, then a deterministic no-op filter), R15 (2 Haiku failures + 1 Gate B regression), R31 (closing-sentence failure; a real probe overturned a reviewer finding, R31:152), R30 (invented-id lapse).
- Live evals: R12 (assertion false positive, driver join bug, fixture bug, real prompt failures).
- Post-merge human use: R15 → ticket 31.

Mocked specs could not have caught most of these: prompt behavior, copy in catalogues, model-visible tool output, provider stream shapes (R31:152, and experiment 01 notes a reviewer "proved" a wrong finding against the SDK adapter, `results.md:9`). But the logs also show runtime checks fail when their inputs are unrealistic (R15's 2-step case vs an 8-step real request).

Ordering matters too. In R29 the browser check ran before the live eval that would have caught the "spouse" lapse (R29:131, :159).

---

## 7. Cross-ticket problems

- **Requirement between tickets:** output cap (ticket 07) vs op-union size (R15). No ticket owned "a large proposal fits", and it escaped to 31.
- **Spec drift across tickets:** R15's paid-prompt change invalidated R12's eval case (fixed in R32). R13 documented the 30k code value against the spec's 50k (R13:41) and R24 carries the rationale. R31 updated SPEC.md caps by hand (R31:123).
- **Rework of an earlier ticket's code:** R14 Gate A design reversed in-run (R14:173). R31's chip reworked by ticket 34 within a day. R12's Language paragraph rewritten again by R26. R14's AgentService split out as R25.
- **Handoffs that worked:** R15's deferred Bugs Important became an acceptance line in ticket 16 (R15:162). R31's deferred silent-turn finding became ticket 33. R12's deferred findings became tickets 26–29. R30's pre-existing bugs became two tickets.
- **Parallel-session coupling:** 4 sessions on 10-31 (15, 25, 28, 29), coordinated by a fifth (sidedoor-39). This produced merge-order constraints (R29:21), repeated rebases (R29:169-172), shared manual-check slots (R15:168-171), and load flakes in every BASE capture (§3). R28's classifier change flipped a committed eval result (R28:67), which R26's baseline now inherits.

---

## 8. Orchestrator (Claude) decisions that later mattered

- Plan errors that surfaced as rejections: R29:89, R31:56, RS:68/74-76, R12:91 (seed default), R16:99.
- Escalation options offered after narrow validation (RM:49 → RM:56).
- Self-justified "rejected: intentional" on its own plan call (R16:113) → rule SKILL:203 the same day.
- Verification lapses it admitted: "I read only the +/- lines" (R15:154); a fixture-reason red passed as behavioral (R16:101).
- Unilateral UX choice after 3 unanswered asks (R14:146).
- Executor work done by hand: Prettier reverts and a CLAUDE.md rule (R14:165-166), prettier on 4 files (R12:125), docstring fix (RH:129). Small, but it contradicts SKILL:11.
- Strong calls that held up: a real-model probe overturned a reviewer (R31:152, confirmed by experiment 01); a body-equivalence script for the pure move (R25:72); an offline re-grade tool (R28:22).

---

## 9. Surprising

1. **Zero `escaped` lines** in a pipeline that defines them, despite at least four clear cases. The retro's data source for review quality is therefore empty by construction.
2. **Executors are not the bottleneck.** 7 step-ups across 20 runs, and most "rejections" trace to the plan, the sandbox or the environment, not to codex.
3. **The eval "gate" doesn't gate.** It was committed red (R12:147), later runs commit with known flakes (R29:164, R32:99), and the prompt changes it judged were measured once until R26.
4. **One ticket (R14) produced ~65% of all Gate B requests** and ran 7 days. Its Gate B absorbed design, UX prototyping, refactors and a new seam, the work a plan or a second ticket normally holds.
5. **Run logs are incomplete in ways the retro can't see.** R14 has no commit or finish. R16 has no wrap-up although a retro ran. Run 34 has no run file. RH's file was lost and rebuilt from the transcript (RH:109).
6. **Reviewer recall on real past catches was 0/3 in a controlled re-run** (experiment 01), which suggests the per-ticket review is a lottery more than a filter.
