#!/usr/bin/env node

// Stop hook: at the end of each turn, scan for git repos under this
// multi-project workspace root (up to 2 levels deep) that have uncommitted
// changes, and for each one run a real Codex adversarial review, leaving the
// conclusion as a markdown file under ~/.claude/codex-reviews/<repo-name>/.
//
// ALLOW (verdict: approve) -> stop proceeds.
// BLOCK (verdict: needs-attention, or the review itself errors/times out)
// -> stop is blocked with the findings fed back, so Claude fixes and retries.
// Silent no-op when there are no dirty repos.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const REVIEW_TIMEOUT_MS = 15 * 60 * 1000;
const MAX_DEPTH = 2;
const MAX_FINDINGS_IN_REASON = 5;
const MAX_REVIEW_FILES_PER_REPO = 20;
const SKIP_DIRS = new Set(["node_modules", ".git", ".claude", "dist", "build", ".vscode", ".idea"]);

function readHookInput() {
  const raw = fs.readFileSync(0, "utf8").trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function emitDecision(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

function logNote(message) {
  if (message) process.stderr.write(`${message}\n`);
}

function git(cwd, args) {
  return spawnSync("git", args, { cwd, encoding: "utf8" });
}

function isGitRepo(dir) {
  const result = git(dir, ["rev-parse", "--is-inside-work-tree"]);
  return result.status === 0 && result.stdout.trim() === "true";
}

function hasChanges(dir) {
  const result = git(dir, ["status", "--short", "--untracked-files=all"]);
  return (result.stdout ?? "").trim().length > 0;
}

function findGitRepos(root, depth = MAX_DEPTH) {
  const repos = [];
  if (isGitRepo(root)) {
    repos.push(root);
    return repos;
  }
  if (depth <= 0) return repos;

  let entries;
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return repos;
  }

  for (const entry of entries) {
    if (!entry.isDirectory() || SKIP_DIRS.has(entry.name) || entry.name.startsWith(".")) continue;
    repos.push(...findGitRepos(path.join(root, entry.name), depth - 1));
  }
  return repos;
}

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

/**
 * Runs `codex adversarial-review` against a repo's working tree.
 * Returns { verdict: "approve"|"needs-attention", summary, findings }.
 * Fails closed: any condition that prevents a real review (no plugin,
 * timeout, bad output) comes back as "needs-attention", never a silent
 * pass-through — a gate that can't verify anything isn't a gate.
 */
function runAdversarialReview(cwd) {
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;
  if (!pluginRoot) {
    return {
      verdict: "needs-attention",
      summary: "CLAUDE_PLUGIN_ROOT is not set (Codex plugin not loaded) — cannot verify changes, failing closed.",
      findings: []
    };
  }

  const scriptPath = path.join(pluginRoot, "scripts", "codex-companion.mjs");
  const focusText = "请用中文撰写本次审查结果：summary 以及每条 finding 的 title/body/recommendation 都要写中文。";
  const result = spawnSync(
    process.execPath,
    [scriptPath, "adversarial-review", "--json", "--scope", "working-tree", focusText],
    { cwd, encoding: "utf8", timeout: REVIEW_TIMEOUT_MS }
  );

  if (result.error?.code === "ETIMEDOUT") {
    return { verdict: "needs-attention", summary: "Codex adversarial review timed out after 15 minutes.", findings: [] };
  }

  if (result.status !== 0) {
    const detail = String(result.stderr || result.stdout || "").trim();
    return {
      verdict: "needs-attention",
      summary: detail ? `Codex adversarial review failed: ${detail}` : "Codex adversarial review failed to run.",
      findings: []
    };
  }

  let payload;
  try {
    payload = JSON.parse(result.stdout);
  } catch {
    return { verdict: "needs-attention", summary: "Codex adversarial review returned invalid JSON output.", findings: [] };
  }

  const parsed = payload?.result;
  if (!parsed?.verdict) {
    return { verdict: "needs-attention", summary: "Codex adversarial review returned no verdict.", findings: [] };
  }

  return { verdict: parsed.verdict, summary: parsed.summary, findings: parsed.findings ?? [] };
}

function reviewFileContent(repoDir, review) {
  const findingLines = (review.findings ?? [])
    .map((f) => `- [${f.severity}] ${f.title} (${f.file}:${f.line_start})\n  ${f.recommendation ?? ""}`)
    .join("\n");

  return [
    "# Codex Review",
    "",
    `- Target: working tree diff`,
    `- Repo: ${repoDir}`,
    `- Generated: ${new Date().toISOString()}`,
    `- Verdict: ${review.verdict ?? "skipped"}`,
    "",
    review.summary ?? review.text ?? "",
    findingLines,
    ""
  ]
    .filter((line) => line !== undefined)
    .join("\n");
}

function pruneOldReviewFiles(dir) {
  let entries;
  try {
    entries = fs
      .readdirSync(dir)
      .filter((name) => name.startsWith("review-") && name.endsWith(".md"))
      .sort();
  } catch {
    return;
  }
  const excess = entries.length - MAX_REVIEW_FILES_PER_REPO;
  if (excess <= 0) return;
  for (const name of entries.slice(0, excess)) {
    try {
      fs.unlinkSync(path.join(dir, name));
    } catch {
      // best-effort cleanup, not worth failing the hook over
    }
  }
}

function writeReviewFile(repoDir, review) {
  // 报告写到集中目录而不是被审查仓库内部，避免审查本身弄脏仓库、
  // 导致下一次 Stop 又触发审查的自我维持循环
  const dir = path.join(os.homedir(), ".claude", "codex-reviews", path.basename(repoDir));
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `review-${timestamp()}.md`);
  fs.writeFileSync(file, reviewFileContent(repoDir, review));
  pruneOldReviewFiles(dir);
  return file;
}

function main() {
  const input = readHookInput();
  const root = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();

  const dirtyRepos = findGitRepos(root).filter(hasChanges);
  if (dirtyRepos.length === 0) {
    return;
  }

  const blockedReasons = [];

  for (const repoDir of dirtyRepos) {
    const review = runAdversarialReview(repoDir);
    const file = writeReviewFile(repoDir, review);
    logNote(`Codex review (${review.verdict}) written to ${file}`);

    if (review.verdict !== "approve") {
      const findingLines = (review.findings ?? [])
        .slice(0, MAX_FINDINGS_IN_REASON)
        .map((f) => `- [${f.severity}] ${f.title} (${f.file}:${f.line_start})`)
        .join("\n");
      blockedReasons.push(
        [`${path.basename(repoDir)}: ${review.summary}`, findingLines].filter(Boolean).join("\n")
      );
    }
  }

  if (blockedReasons.length > 0) {
    emitDecision({
      decision: "block",
      reason: ["Codex adversarial review (BLOCK) found unresolved issues before stopping:", ...blockedReasons].join(
        "\n\n"
      )
    });
  }
}

try {
  main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
}
