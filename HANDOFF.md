# HANDOFF — `~/Applications/ApopheniaBoricua-master`

Owner: the Human Architect (HA). Writer: this directory's session (started from `~/Applications/ApopheniaBoricua-master`).
Parent: `~/Desktop/HANDOFF_CAMPAIGN_REGION.md`.
Handed over from the Multi-Agent-LLM session to the campaign region under CM-3 (D3), 2026-11-12.
Last updated: 2026-11-13 (first version; CM-3 order from the campaign session; HA yes 1 plan, yes 2 old → new, yes 3 write and commit).
Audience: the next Claude Code / Codex session in this folder, and the HA.

Session start (H-9): new work starts in a fresh `claude` from this handoff.

## Next session starts here

**Start checks (read only, expected result):**
- `git log --oneline -1` → the commit that last changed this file (`git log -1 --format=%h -- HANDOFF.md`; it cannot name itself), on `3edad16`.
- `git status -sb` → `## main...origin/main [ahead 1]` until a push, then 4 untracked lines: `ApopheniaBoricua-master/`, `FeeDesktopDbus-master/`, `public/images/lattice-design.png`, `public/slides.html`.
- `git remote get-url origin` → `https://github.com/Eziknmad/ApopheniaBoricua-master.git`.
- `sha256sum public/index.html public/style.css public/slides.html` → `6ba0b78d…`, `9f0a3da7…`, `d4776023…`.
- `grep -n "Nov 8\|November 8" public/index.html` → nothing.
Then confirm with the HA what to work on. Nothing is authorized by this note.

**Unfinished work (item → owner → what is needed):**
- Demo video URL → HA → the HA records the video; then one line in `public/index.html` (the disabled button at `:34-35`, `[YOUTUBE_URL]` comment) and a new item on the intranet.
- Publish on GitHub Pages → HA → separate yes (CM-3 Part D). On 2026-11-13 `https://github.com/Eziknmad/ApopheniaBoricua-master` answered 404 to a signed-out request, so the repository link on the page does not open for visitors yet.
- Repository sentence at `public/index.html:142` → HA → it says "The landing page's source is in the project repository on GitHub" today, because this repository holds the landing page only. When the app code is pushed (LP-7, separate HA yes), change the sentence and the link to point at the apps' code. No change to the page until then.
- X profile link when the HA has an account → HA → left out for now with no placeholder (HA, 2026-11-13). The intranet task asks for a Twitter profile link; add it next to LinkedIn and GitHub at `public/index.html:147` once the HA gives the URL.
- `public/images/lattice-design.png` → HA → left out of the commit (HA, 2026-11-13); not used by `index.html`.
- `ApopheniaBoricua-master/`, `FeeDesktopDbus-master/`, `public/slides.html` (all untracked) → HA decides. Never stage `FeeDesktopDbus-master/`.
- Manual QA review → HA → request it from a peer, TA or staff member on the intranet.
- LinkedIn link → HA → not testable by script (HTTP 999); open it once in a browser.
- MT-1: no parallel workers or subagents until the HA closes it.

## Current state (checked on disk 2026-11-13)

- `public/` is the landing page for the Holberton "Portfolio Project - Landing Page" project:
  - `index.html`: the page (intro, 3 features, research case, evidence table, about).
  - `style.css`: its stylesheet.
  - `images/`: 5 PNGs (`bunkhouse`, `lattice-design`, `orchestrator`, `trading`, `tutor`); `index.html` uses 4, not `lattice-design.png`.
  - `slides.html`: the Stage 5 slides (talk Nov 9, `slides.html:68`, `:71`).
- Page vs the four intranet tasks:
  - Task 0 intro: met, except the button is disabled ("coming soon") because no demo video exists.
  - Task 1 features: met.
  - Task 2 about: story, timeline, Holberton School link, LinkedIn, GitHub profile and repository link present; no Twitter/X.
  - Task 3 deliverables: no landing page URL and no video yet.
- Tracked: `public/index.html`, `public/style.css`, 4 PNGs in `public/images/`, `HANDOFF.md`, `README.md`, `.gitignore`, `.gitlab-ci.yml`, `.gitmodules`, `.github/`, `engine-contract/`, `my-app/`, `my-awesome-site/`, `PareidoliaBoricua/`.
- Untracked: `ApopheniaBoricua-master/` and `FeeDesktopDbus-master/` (both nested git folders dated 2026-07-09), `public/slides.html`, `public/images/lattice-design.png`.
- `FeeDesktopDbus-master/` holds `config`, `id_ed25519.pub`, `known_hosts.old` and an empty `README.md` (names listed only, not opened).
- `.gitignore` keeps `.claude/`, `.env*`, `node_modules/` and build folders out of git.
- `.github/` holds only `copilot-instructions.md` (no workflows). `.gitlab-ci.yml` is a GitLab Pages template that serves `public/`; it runs on GitLab only, and origin is GitHub.
- `.gitmodules` names one submodule: `PareidoliaBoricua/FeeDesktopDbus-master` (GitLab, SSH URL).
- Not published: nothing pushed since `3edad16`.

## Handoff chain (read in this order)
1. `~/Desktop/HANDOFF_CAMPAIGN_REGION.md` (region rules, FACT format, hard rules).
2. This file.
3. The saved project page (read only): `~/Desktop/DemoDirectory/Holberton-io/Portfolio Project v2/Project_ Portfolio Project - Landing Page _ Holberton Aguadilla, Puerto Rico Intranet.html`.
AI-chat notes and ChatGPT Desktop / Codex output are input, not authority.

## Read / write rules
- **Read:** this folder; the chain above; other folders read only, and only when a task names them.
- **Write:** only inside `~/Applications/ApopheniaBoricua-master`, each change with the HA's yes (yes 1 plan → yes 2 old → new → yes 3 write or commit). Not the vault, not region files, not the trading, tutor, DemoDirectory or Multi-Agent-LLM folders.
- `git add` names its files; never `git add -A` or `git add .`.
- Questions go to the campaign session through the HA.

## Hard rules
- Nothing is pushed or made public without the HA's separate publish yes. A push is plain `git push origin main`: no force push, no history rewrite, no branch deletion, no other repo. LP-7 stays closed for the tutor and BunkHouseChess.
- Never open credential, session or token files. Never stage `FeeDesktopDbus-master/`. Never run `gitauto.sh`. No Atlas cloud.
- No profit claims; the trading text on the page stays as it is. No new claims, numbers or screenshots without the HA; a missing fact is asked, not filled in.
- One session for this program (MT-1); no subagents, no parallel workers. Co-author line per CO-1.
- The project is complete only when the HA says so.

## FACT format
`FACT: <what changed> | PROOF: <path or commit> | NEEDS HA: yes/no (tested/untested) | MODEL: <model id>`
Add `| DRIFT: <file:line>` when a file disagrees with the disk.

## Session log
- 2026-11-13: first session under CM-3 (campaign region order; HA yes 1, yes 2, yes 3). Start checks matched the campaign session's values. `public/index.html`: Nov 8 → Nov 9 (`:29`, `:141`), Holberton School link and repository link (`:142`), GitHub profile link (`:147`); button and note unchanged. Page checked at 1440 px and 390 px. This file written. Committed with `public/style.css` and 4 PNGs; no push.
