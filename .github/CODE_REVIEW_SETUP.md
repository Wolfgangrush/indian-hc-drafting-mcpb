# AI Code Review Setup

Pilot of the PR-gated AI review pipeline for the wolfgang_rush MCPB family.
This repo is the first one; replicate the same workflow + branch protection
in the other 13 MCPB repos + the AI Law Firm jurisdictional repos after
two clean weeks here.

## What this gives you

- Every PR opened against `main` triggers `.github/workflows/ai-code-review.yml`.
- Claude reviews the diff against main using the prompt in the workflow file
  (SQL safety · LLM trust boundary · DPDP leakage · secrets · MCPB-specific
  · self-representation integrity).
- Findings post as inline PR review comments.
- If any finding is rated CRITICAL, the workflow exits non-zero and the
  required status check blocks merge.

## One-time setup (do this once)

### 1. Install the Claude Code GitHub App on this repo

This pilot uses the Claude Code GitHub App for auth — no `ANTHROPIC_API_KEY`
secret needed. The App routes review calls through your Claude Max
subscription instead of pay-per-token API billing.

Install at: https://github.com/apps/claude (verify current URL in
Anthropic's Claude Code GitHub docs — the App name may differ slightly).
Authorize it on `Wolfgangrush/indian-hc-drafting-mcpb` only (not org-wide
unless you also want it on the other 12 MCPB repos when you replicate the
pilot).

If the first workflow run errors with "no auth available", the App install
may also need to expose a `CLAUDE_CODE_OAUTH_TOKEN` repo secret — follow
the App's setup prompts and re-trigger the workflow.

### 2. Verify the action's input names

`anthropics/claude-code-action@beta` is the official action but the @beta
tag moves. Open one test PR (any trivial change) to confirm the workflow
runs. If inputs have been renamed (e.g. `anthropic_api_key` → `api_key`),
the workflow logs will surface the error — fix and re-run.

Once the workflow runs cleanly once, pin to a specific commit SHA:

```bash
# Find the SHA of the version that worked
gh api repos/anthropics/claude-code-action/commits/beta --jq '.sha' | head -c 12

# Then edit .github/workflows/ai-code-review.yml and replace
#   uses: anthropics/claude-code-action@beta
# with:
#   uses: anthropics/claude-code-action@<sha>
```

### 3. Turn on branch protection on main

```bash
gh api -X PUT \
  "repos/Wolfgangrush/indian-hc-drafting-mcpb/branches/main/protection" \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]="Claude review" \
  -f enforce_admins=false \
  -f required_pull_request_reviews[required_approving_review_count]=0 \
  -f required_pull_request_reviews[dismiss_stale_reviews]=true \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

Notes:
- `enforce_admins=false` lets you push direct-to-main from your account in
  an emergency. Flip to `true` after the pilot stabilises.
- `required_approving_review_count=0` because you're solo — only the AI
  reviewer gates merge. Bump to 1 when you have a human collaborator.
- The context name `"Claude review"` must match the workflow's `job.name`
  exactly. If you rename the job, update this command.

### 4. Test the gate

Open a deliberately-broken PR. Suggested test:

```bash
git checkout -b test/ai-review-smoke
echo 'API_KEY = "sk-ant-test-fake-key-do-not-use"' >> server/__main__.py
git add server/__main__.py
git commit -m "smoke: deliberately leak a fake key to test the gate"
git push -u origin test/ai-review-smoke
gh pr create --title "smoke test: AI review gate" --body "Should be blocked."
```

Expected: AI review posts a CRITICAL on the hardcoded key, workflow exits
non-zero, merge button greyed out. Close the PR + delete the branch when done.

## How to extend this to the other 12 MCPB repos + AI Law Firm repos

After two clean weeks (no false-positive merge blocks):

```bash
# Loop over the MCPB family repos
for repo in \
  wolfgang-indian-mact-drafting \
  wolfgang-indian-ip-drafting \
  wolfgang-indian-tax-drafting \
  wolfgang-indian-rent-control-drafting \
  wolfgang-indian-labour-drafting \
  wolfgang-district-court-drafting \
  wolfgang-indian-consumer-drafting \
  wolfgang-supreme-court-drafting \
  wolfgang-indian-property-drafting \
  wolfgang-indian-banking-drafting \
  wolfgang-indian-company-drafting \
  wolfgang-indian-family-drafting \
  wolfgang-indian-contracts-drafting
do
  cp -r .github "../$repo/"
  echo "copied workflow into $repo — open PR to enable"
done
```

Then run step 1 + step 3 on each repo via `gh`.

## What this does NOT do (yet)

- No telemetry on review quality. You'll manually judge whether Claude's
  findings are landing or just adding noise.
- No bypass for trivial PRs (typos / README-only / docs-only). If review
  noise is high, add a `paths-ignore: ['**/*.md']` filter to the `on:`
  trigger.
- No multi-model fan-out. One reviewer = one perspective.
- No interaction with the local `/lawtech-code-review` skill. The two
  pipelines run independently — local pre-push, GitHub on PR.

## When to fix vs when to bypass

If Claude flags something CRITICAL that's a false positive:

1. Reply to the inline comment explaining why.
2. Push an empty commit (`git commit --allow-empty -m "re-run review"`)
   to re-trigger. If Claude still flags it, refine your fix or:
3. Last resort — temporarily drop the required-status-check requirement
   via `gh` (re-add it after merge). Never merge with a CRITICAL standing.

CRITICAL bypass should happen <1 PR/month. If it happens more, the prompt
in the workflow needs sharpening, not the gate loosening.
