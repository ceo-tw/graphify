#!/usr/bin/env node
/**
 * PreToolUse Hook: GateGuard Fact-Forcing Gate
 *
 * Forces agents to investigate before editing files or running commands.
 * Instead of asking "are you sure?", demands concrete facts:
 * importers, public API, data schemas, and determinism-pipeline impact.
 *
 * Gates:
 *   - Edit/Write: list importers, affected API, verify pipeline invariants, quote instruction
 *   - Bash (destructive): list targets, rollback plan, quote instruction
 *   - Bash (routine): quote current instruction (once per session)
 *
 * Adapted from ECC GateGuard for graphify (Python CLI + library).
 * Gates editing of the deterministic pipeline surface and destructive bash.
 */

'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const STATE_DIR = process.env.GATEGUARD_STATE_DIR || path.join(process.env.HOME || process.env.USERPROFILE || '/tmp', '.gateguard');
const SESSION_ID = process.env.CLAUDE_SESSION_ID || process.env.ECC_SESSION_ID || `pid-${process.ppid || process.pid}`;
const STATE_FILE = path.join(STATE_DIR, `state-${SESSION_ID.replace(/[^a-zA-Z0-9_-]/g, '_')}.json`);

const SESSION_TIMEOUT_MS = 30 * 60 * 1000;
const MAX_CHECKED_ENTRIES = 500;
const MAX_SESSION_KEYS = 50;
const ROUTINE_BASH_SESSION_KEY = '__bash_session__';

const DESTRUCTIVE_BASH = /\b(rm\s+-rf|git\s+reset\s+--hard|git\s+checkout\s+--|git\s+clean\s+-f|drop\s+table|delete\s+from|truncate|git\s+push\s+--force|dd\s+if=)\b/i;

// Only gate Edit/Write for sensitive graphify files:
//   - the deterministic pipeline (extract / build / routes / http_calls / analyze / cli_graph_query / cache)
//   - security boundary modules (security / ingest / transcribe / serve / hooks / detect)
//   - packaging surface (pyproject.toml at repo root)
const SENSITIVE_PATHS = /graphify\/(extract|build|routes|http_calls|analyze|cli_graph_query|cache|security|ingest|transcribe|serve|hooks|detect)\.py$|(^|\/)pyproject\.toml$/i;

// --- State management ---

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      if (Date.now() - (state.last_active || 0) > SESSION_TIMEOUT_MS) {
        try { fs.unlinkSync(STATE_FILE); } catch (_) { /* ignore */ }
        return { checked: [], last_active: Date.now() };
      }
      return state;
    }
  } catch (_) { /* ignore */ }
  return { checked: [], last_active: Date.now() };
}

function pruneCheckedEntries(checked) {
  if (checked.length <= MAX_CHECKED_ENTRIES) return checked;
  const preserved = checked.includes(ROUTINE_BASH_SESSION_KEY) ? [ROUTINE_BASH_SESSION_KEY] : [];
  const sessionKeys = checked.filter(k => k.startsWith('__') && k !== ROUTINE_BASH_SESSION_KEY);
  const fileKeys = checked.filter(k => !k.startsWith('__'));
  const cappedSession = sessionKeys.slice(-(Math.max(MAX_SESSION_KEYS - preserved.length, 0)));
  const cappedFiles = fileKeys.slice(-(Math.max(MAX_CHECKED_ENTRIES - preserved.length - cappedSession.length, 0)));
  return [...preserved, ...cappedSession, ...cappedFiles];
}

function saveState(state) {
  try {
    state.last_active = Date.now();
    state.checked = pruneCheckedEntries(state.checked);
    fs.mkdirSync(STATE_DIR, { recursive: true });
    const tmpFile = STATE_FILE + '.tmp.' + process.pid;
    fs.writeFileSync(tmpFile, JSON.stringify(state, null, 2), 'utf8');
    fs.renameSync(tmpFile, STATE_FILE);
  } catch (_) { /* ignore */ }
}

function markChecked(key) {
  const state = loadState();
  if (!state.checked.includes(key)) {
    state.checked.push(key);
    saveState(state);
  }
}

function isChecked(key) {
  const state = loadState();
  const found = state.checked.includes(key);
  saveState(state);
  return found;
}

// Prune stale session files
(function pruneStaleFiles() {
  try {
    const files = fs.readdirSync(STATE_DIR);
    const now = Date.now();
    for (const f of files) {
      if (!f.startsWith('state-') || !f.endsWith('.json')) continue;
      const fp = path.join(STATE_DIR, f);
      const stat = fs.statSync(fp);
      if (now - stat.mtimeMs > SESSION_TIMEOUT_MS * 2) fs.unlinkSync(fp);
    }
  } catch (_) { /* ignore */ }
})();

function sanitizePath(filePath) {
  return filePath.replace(/[\x00-\x1f\x7f\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, ' ').trim().slice(0, 500);
}

// --- Gate messages (graphify customized) ---

function editGateMsg(filePath) {
  const safe = sanitizePath(filePath);
  return [
    '[Fact-Forcing Gate]',
    '',
    `Before editing ${safe}, present these facts:`,
    '',
    '1. List ALL files that import this module (use Grep on `from graphify.<mod>`/`import graphify.<mod>`)',
    '2. List the public functions/classes affected by this change',
    '3. If this module is on the deterministic pipeline, confirm no wall-clock / random / eval is introduced',
    '4. If edge tags are touched, confirm the vocabulary stays {EXTRACTED, INFERRED, AMBIGUOUS} or CHANGELOG updated',
    '5. Quote the user\'s current instruction verbatim',
    '',
    'Present the facts, then retry the same operation.'
  ].join('\n');
}

function writeGateMsg(filePath) {
  const safe = sanitizePath(filePath);
  return [
    '[Fact-Forcing Gate]',
    '',
    `Before creating ${safe}, present these facts:`,
    '',
    '1. Name the file(s) and line(s) that will call this new module',
    '2. Confirm no existing graphify module serves the same purpose (use Glob on graphify/*.py)',
    '3. If this module uses optional extras (faster-whisper / pypdf / neo4j / mcp), is the import gated behind try/ImportError?',
    '4. Quote the user\'s current instruction verbatim',
    '',
    'Present the facts, then retry the same operation.'
  ].join('\n');
}

function destructiveBashMsg() {
  return [
    '[Fact-Forcing Gate]',
    '',
    'Destructive command detected. Before running, present:',
    '',
    '1. List all files/data this command will modify or delete',
    '2. Write a one-line rollback procedure',
    '3. Quote the user\'s current instruction verbatim',
    '',
    'Present the facts, then retry the same operation.'
  ].join('\n');
}

function routineBashMsg() {
  return [
    '[Fact-Forcing Gate]',
    '',
    'Quote the user\'s current instruction verbatim.',
    'Then retry the same operation.'
  ].join('\n');
}

// --- Deny helper ---

function denyResult(reason) {
  return {
    stdout: JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reason
      }
    }),
    exitCode: 0
  };
}

// --- Core logic ---

function run(rawInput) {
  let data;
  try {
    data = typeof rawInput === 'string' ? JSON.parse(rawInput) : rawInput;
  } catch (_) {
    return rawInput;
  }

  const rawToolName = data.tool_name || '';
  const toolInput = data.tool_input || {};
  const TOOL_MAP = { 'edit': 'Edit', 'write': 'Write', 'multiedit': 'MultiEdit', 'bash': 'Bash' };
  const toolName = TOOL_MAP[rawToolName.toLowerCase()] || rawToolName;

  if (toolName === 'Edit' || toolName === 'Write') {
    const filePath = toolInput.file_path || '';
    if (!filePath) return rawInput;

    // Only gate sensitive files; allow general Edit/Write without blocking
    if (!SENSITIVE_PATHS.test(filePath)) return rawInput;

    if (!isChecked(filePath)) {
      markChecked(filePath);
      return denyResult(toolName === 'Edit' ? editGateMsg(filePath) : writeGateMsg(filePath));
    }
    return rawInput;
  }

  if (toolName === 'MultiEdit') {
    const edits = toolInput.edits || [];
    for (const edit of edits) {
      const filePath = edit.file_path || '';
      // Only gate sensitive files
      if (filePath && SENSITIVE_PATHS.test(filePath) && !isChecked(filePath)) {
        markChecked(filePath);
        return denyResult(editGateMsg(filePath));
      }
    }
    return rawInput;
  }

  if (toolName === 'Bash') {
    const command = toolInput.command || '';

    if (DESTRUCTIVE_BASH.test(command)) {
      const key = '__destructive__' + crypto.createHash('sha256').update(command).digest('hex').slice(0, 16);
      if (!isChecked(key)) {
        markChecked(key);
        return denyResult(destructiveBashMsg());
      }
      return rawInput;
    }

    // Routine bash gate removed - only destructive commands are blocked
    return rawInput;
  }

  return rawInput;
}

module.exports = { run };
