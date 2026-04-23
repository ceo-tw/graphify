#!/usr/bin/env node
/**
 * Config Protection Hook
 *
 * Blocks modifications to linter/formatter/build config files.
 * Agents frequently modify these to make checks pass instead of fixing
 * the actual code. This hook steers the agent back to fixing the source.
 *
 * Exit codes:
 *   0 = allow (not a config file)
 *   2 = block (config file modification attempted)
 */

'use strict';

const path = require('path');

const MAX_STDIN = 1024 * 1024;
let raw = '';

const PROTECTED_FILES = new Set([
  // ESLint
  '.eslintrc', '.eslintrc.js', '.eslintrc.cjs', '.eslintrc.json',
  '.eslintrc.yml', '.eslintrc.yaml',
  'eslint.config.js', 'eslint.config.mjs', 'eslint.config.cjs',
  'eslint.config.ts', 'eslint.config.mts', 'eslint.config.cts',
  // Prettier
  '.prettierrc', '.prettierrc.js', '.prettierrc.cjs',
  '.prettierrc.json', '.prettierrc.yml', '.prettierrc.yaml',
  'prettier.config.js', 'prettier.config.cjs', 'prettier.config.mjs',
  // Biome
  'biome.json', 'biome.jsonc',
  // TypeScript config
  'tsconfig.json', 'tsconfig.build.json',
  // Next.js config
  'next.config.js', 'next.config.mjs', 'next.config.ts',
  // Database config
  'drizzle.config.ts',
  // UI config (shadcn/ui)
  'components.json',
  // Test config
  'vitest.config.ts', 'vitest.config.mts',
  // CSS config
  'tailwind.config.ts', 'tailwind.config.js',
  'postcss.config.js', 'postcss.config.mjs',
  // Style/Markdown
  '.stylelintrc', '.stylelintrc.json', '.stylelintrc.yml',
  '.markdownlint.json', '.markdownlint.yaml', '.markdownlintrc',
]);

function run(inputOrRaw, options = {}) {
  if (options.truncated) {
    return {
      exitCode: 2,
      stderr:
        `BLOCKED: Hook input exceeded ${options.maxStdin || MAX_STDIN} bytes. ` +
        'Refusing to bypass config-protection on a truncated payload.'
    };
  }

  let input;
  if (typeof inputOrRaw === 'string') {
    try { input = inputOrRaw.trim() ? JSON.parse(inputOrRaw) : {}; } catch { input = {}; }
  } else {
    input = inputOrRaw && typeof inputOrRaw === 'object' ? inputOrRaw : {};
  }

  const filePath = input?.tool_input?.file_path || input?.tool_input?.file || '';
  if (!filePath) return { exitCode: 0 };

  const basename = path.basename(filePath);
  if (PROTECTED_FILES.has(basename)) {
    return {
      exitCode: 2,
      stderr:
        `BLOCKED: ${basename} 수정이 차단되었습니다. / Modifying ${basename} is not allowed. ` +
        'Fix the source code to satisfy linter/formatter rules instead of ' +
        'weakening the config.',
    };
  }

  return { exitCode: 0 };
}

module.exports = { run };

// Stdin fallback for spawnSync execution
let truncated = /^(1|true|yes)$/i.test(String(process.env.ECC_HOOK_INPUT_TRUNCATED || ''));
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  if (raw.length < MAX_STDIN) {
    const remaining = MAX_STDIN - raw.length;
    raw += chunk.substring(0, remaining);
    if (chunk.length > remaining) truncated = true;
  } else {
    truncated = true;
  }
});

process.stdin.on('end', () => {
  const result = run(raw, { truncated, maxStdin: MAX_STDIN });
  if (result.stderr) process.stderr.write(result.stderr + '\n');
  if (result.exitCode === 2) process.exit(2);
  process.stdout.write(raw);
});
