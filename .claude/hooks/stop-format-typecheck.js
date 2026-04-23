#!/usr/bin/env node
/**
 * Stop Hook: Batch format and typecheck all JS/TS files edited this response
 *
 * Reads the accumulator written by post-edit-accumulator.js and processes all
 * edited files in one pass: groups files by project root for a single formatter
 * invocation per root, and groups .ts/.tsx files by tsconfig dir for a single
 * tsc --noEmit per tsconfig.
 */

'use strict';

const crypto = require('crypto');
const { execFileSync, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const MAX_STDIN = 1024 * 1024;
const TOTAL_BUDGET_MS = 270_000;

function parseAccumulator(raw) {
  return [...new Set(raw.split('\n').map(l => l.trim()).filter(Boolean))];
}

function getAccumFile() {
  const raw =
    process.env.CLAUDE_SESSION_ID ||
    crypto.createHash('sha1').update(process.cwd()).digest('hex').slice(0, 12);
  const sessionId = raw.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64);
  return path.join(os.tmpdir(), `ocl-edited-${sessionId}.txt`);
}

function findProjectRoot(startDir) {
  let dir = startDir;
  const fsRoot = path.parse(dir).root;
  let depth = 0;
  while (dir !== fsRoot && depth < 20) {
    if (fs.existsSync(path.join(dir, 'package.json'))) return dir;
    dir = path.dirname(dir);
    depth++;
  }
  return startDir;
}

function detectFormatter(projectRoot) {
  if (fs.existsSync(path.join(projectRoot, 'biome.json')) ||
      fs.existsSync(path.join(projectRoot, 'biome.jsonc'))) return 'biome';
  if (fs.existsSync(path.join(projectRoot, '.prettierrc')) ||
      fs.existsSync(path.join(projectRoot, '.prettierrc.json')) ||
      fs.existsSync(path.join(projectRoot, 'prettier.config.js')) ||
      fs.existsSync(path.join(projectRoot, 'prettier.config.mjs'))) return 'prettier';
  if (fs.existsSync(path.join(projectRoot, 'node_modules', '.bin', 'prettier'))) return 'prettier';
  return null;
}

function resolveFormatterBin(projectRoot, formatter) {
  const binDir = path.join(projectRoot, 'node_modules', '.bin');
  const bin = path.join(binDir, formatter);
  if (fs.existsSync(bin)) return { bin, prefix: [] };
  return null;
}

function formatBatch(projectRoot, files, timeoutMs) {
  const formatter = detectFormatter(projectRoot);
  if (!formatter) return;
  const resolved = resolveFormatterBin(projectRoot, formatter);
  if (!resolved) return;

  const existingFiles = files.filter(f => fs.existsSync(f));
  if (existingFiles.length === 0) return;

  const fileArgs = formatter === 'biome'
    ? [...resolved.prefix, 'check', '--write', ...existingFiles]
    : [...resolved.prefix, '--write', ...existingFiles];

  try {
    execFileSync(resolved.bin, fileArgs, {
      cwd: projectRoot, stdio: ['pipe', 'pipe', 'pipe'], timeout: timeoutMs
    });
  } catch {
    // Formatter not installed or failed — non-blocking
  }
}

function findTsConfigDir(filePath) {
  let dir = path.dirname(filePath);
  const fsRoot = path.parse(dir).root;
  let depth = 0;
  while (dir !== fsRoot && depth < 20) {
    if (fs.existsSync(path.join(dir, 'tsconfig.json'))) return dir;
    dir = path.dirname(dir);
    depth++;
  }
  return null;
}

function typecheckBatch(tsConfigDir, editedFiles, timeoutMs) {
  const npxBin = process.platform === 'win32' ? 'npx.cmd' : 'npx';
  const args = ['tsc', '--noEmit', '--pretty', 'false'];
  const opts = { cwd: tsConfigDir, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], timeout: timeoutMs };

  try {
    execFileSync(npxBin, args, opts);
  } catch (err) {
    const lines = ((err.stdout || '') + (err.stderr || '')).split('\n');
    for (const filePath of editedFiles) {
      const relPath = path.relative(tsConfigDir, filePath);
      const candidates = new Set([filePath, relPath]);
      const relevantLines = lines
        .filter(line => { for (const c of candidates) { if (line.includes(c)) return true; } return false; })
        .slice(0, 10);
      if (relevantLines.length > 0) {
        process.stderr.write(`[StopCheck] TypeScript errors in ${path.basename(filePath)}:\n`);
        relevantLines.forEach(line => process.stderr.write(line + '\n'));
      }
    }
  }
}

function main() {
  const accumFile = getAccumFile();
  let raw;
  try { raw = fs.readFileSync(accumFile, 'utf8'); } catch { return; }
  try { fs.unlinkSync(accumFile); } catch { /* best-effort */ }

  const files = parseAccumulator(raw);
  if (files.length === 0) return;

  const byProjectRoot = new Map();
  for (const filePath of files) {
    if (!/\.(ts|tsx|js|jsx)$/.test(filePath)) continue;
    const resolved = path.resolve(filePath);
    if (!fs.existsSync(resolved)) continue;
    const root = findProjectRoot(path.dirname(resolved));
    if (!byProjectRoot.has(root)) byProjectRoot.set(root, []);
    byProjectRoot.get(root).push(resolved);
  }

  const byTsConfigDir = new Map();
  for (const filePath of files) {
    if (!/\.(ts|tsx)$/.test(filePath)) continue;
    const resolved = path.resolve(filePath);
    if (!fs.existsSync(resolved)) continue;
    const tsDir = findTsConfigDir(resolved);
    if (!tsDir) continue;
    if (!byTsConfigDir.has(tsDir)) byTsConfigDir.set(tsDir, []);
    byTsConfigDir.get(tsDir).push(resolved);
  }

  const totalBatches = byProjectRoot.size + byTsConfigDir.size;
  const perBatchMs = totalBatches > 0 ? Math.floor(TOTAL_BUDGET_MS / totalBatches) : 60_000;

  for (const [root, batch] of byProjectRoot) formatBatch(root, batch, perBatchMs);
  for (const [tsDir, batch] of byTsConfigDir) typecheckBatch(tsDir, batch, perBatchMs);
}

function run(rawInput) {
  try { main(); } catch (err) {
    process.stderr.write(`[StopCheck] Error: ${err.message}\n`);
  }
  return rawInput;
}

if (require.main === module) {
  let stdinData = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => {
    if (stdinData.length < MAX_STDIN) stdinData += chunk.substring(0, MAX_STDIN - stdinData.length);
  });
  process.stdin.on('end', () => {
    process.stdout.write(run(stdinData));
    process.exit(0);
  });
}

module.exports = { run, parseAccumulator };
