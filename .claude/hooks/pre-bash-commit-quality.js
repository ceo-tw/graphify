#!/usr/bin/env node
/**
 * PreToolUse Hook: Pre-commit Quality Check
 *
 * Runs quality checks before git commit commands:
 * - Detects staged files
 * - Checks for console.log, debugger, hardcoded secrets
 * - Validates conventional commit message format
 *
 * Exit codes:
 *   0 - Allow commit
 *   2 - Block commit (critical issues found)
 */

'use strict';

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const MAX_STDIN = 1024 * 1024;

function getStagedFiles() {
  const result = spawnSync('git', ['diff', '--cached', '--name-only', '--diff-filter=ACMR'], {
    encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe']
  });
  if (result.status !== 0) return [];
  return result.stdout.trim().split('\n').filter(f => f.length > 0);
}

function getStagedFileContent(filePath) {
  const result = spawnSync('git', ['show', `:${filePath}`], {
    encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe']
  });
  return result.status === 0 ? result.stdout : null;
}

function shouldCheckFile(filePath) {
  return ['.js', '.jsx', '.ts', '.tsx'].some(ext => filePath.endsWith(ext));
}

function findFileIssues(filePath) {
  const issues = [];
  const content = getStagedFileContent(filePath);
  if (!content) return issues;

  const lines = content.split('\n');
  lines.forEach((line, index) => {
    const lineNum = index + 1;

    if (line.includes('console.log') && !line.trim().startsWith('//') && !line.trim().startsWith('*')) {
      issues.push({ type: 'console.log', message: `console.log at line ${lineNum}`, line: lineNum, severity: 'warning' });
    }

    if (/\bdebugger\b/.test(line) && !line.trim().startsWith('//')) {
      issues.push({ type: 'debugger', message: `debugger statement at line ${lineNum}`, line: lineNum, severity: 'error' });
    }

    const secretPatterns = [
      { pattern: /sk-[a-zA-Z0-9]{20,}/, name: 'OpenAI API key' },
      { pattern: /ghp_[a-zA-Z0-9]{36}/, name: 'GitHub PAT' },
      { pattern: /AKIA[A-Z0-9]{16}/, name: 'AWS Access Key' },
      { pattern: /api[_-]?key\s*[=:]\s*['"][^'"]+['"]/i, name: 'API key' }
    ];

    for (const { pattern, name } of secretPatterns) {
      if (pattern.test(line)) {
        issues.push({ type: 'secret', message: `Potential ${name} at line ${lineNum}`, line: lineNum, severity: 'error' });
      }
    }
  });

  return issues;
}

function validateCommitMessage(command) {
  const messageMatch = command.match(/(?:-m|--message)[=\s]+["']?([^"']+)["']?/);
  if (!messageMatch) return null;

  const message = messageMatch[1];
  const issues = [];
  const conventionalCommit = /^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert)(\(.+\))?:\s*.+/;

  if (!conventionalCommit.test(message)) {
    issues.push({ type: 'format', message: 'Not conventional commit format', suggestion: 'Use: type(scope): description' });
  }
  if (message.length > 72) {
    issues.push({ type: 'length', message: `Too long (${message.length} chars, max 72)` });
  }

  return { message, issues };
}

function evaluate(rawInput) {
  try {
    const input = JSON.parse(rawInput);
    const command = input.tool_input?.command || '';

    if (!command.includes('git commit')) return { output: rawInput, exitCode: 0 };
    if (command.includes('--amend')) return { output: rawInput, exitCode: 0 };

    const stagedFiles = getStagedFiles();
    if (stagedFiles.length === 0) {
      process.stderr.write('[CommitCheck] No staged files found.\n');
      return { output: rawInput, exitCode: 0 };
    }

    process.stderr.write(`[CommitCheck] Checking ${stagedFiles.length} staged file(s)...\n`);

    const filesToCheck = stagedFiles.filter(shouldCheckFile);
    let errorCount = 0;
    let warningCount = 0;

    for (const file of filesToCheck) {
      const fileIssues = findFileIssues(file);
      if (fileIssues.length > 0) {
        process.stderr.write(`\n[FILE] ${file}\n`);
        for (const issue of fileIssues) {
          const label = issue.severity === 'error' ? 'ERROR' : 'WARNING';
          process.stderr.write(`  ${label} Line ${issue.line}: ${issue.message}\n`);
          if (issue.severity === 'error') errorCount++;
          else warningCount++;
        }
      }
    }

    const messageValidation = validateCommitMessage(command);
    if (messageValidation && messageValidation.issues.length > 0) {
      process.stderr.write('\nCommit Message Issues:\n');
      for (const issue of messageValidation.issues) {
        process.stderr.write(`  WARNING ${issue.message}\n`);
        if (issue.suggestion) process.stderr.write(`     TIP ${issue.suggestion}\n`);
        warningCount++;
      }
    }

    if (errorCount > 0) {
      process.stderr.write(`\n[CommitCheck] BLOCKED: ${errorCount} error(s), ${warningCount} warning(s). Fix errors before committing.\n`);
      return { output: rawInput, exitCode: 2 };
    } else if (warningCount > 0) {
      process.stderr.write(`\n[CommitCheck] ${warningCount} warning(s). Consider fixing, but commit allowed.\n`);
    } else {
      process.stderr.write('\n[CommitCheck] All checks passed.\n');
    }
  } catch (error) {
    process.stderr.write(`[CommitCheck] Error: ${error.message}\n`);
  }

  return { output: rawInput, exitCode: 0 };
}

function run(rawInput) {
  return evaluate(rawInput).output;
}

if (require.main === module) {
  let data = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => {
    if (data.length < MAX_STDIN) data += chunk.substring(0, MAX_STDIN - data.length);
  });
  process.stdin.on('end', () => {
    const result = evaluate(data);
    process.stdout.write(result.output);
    process.exit(result.exitCode);
  });
}

module.exports = { run, evaluate };
