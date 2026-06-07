#!/usr/bin/env node
/**
 * Generate web/openapi.json from the live FastAPI app schema.
 * Runs as part of `npm run build`.
 */
import { execFileSync, execSync } from 'child_process';
import { writeFileSync, writeFile } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { tmpdir } from 'os';
import { randomBytes } from 'crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '../../');
const outPath = resolve(__dirname, '../openapi.json');
const python = resolve(repoRoot, '.venv/bin/python');
const pyPath = resolve(repoRoot, 'python_server/src');

const script = [
  'import json, sys',
  `sys.path.insert(0, '${pyPath}')`,
  'from unittest.mock import MagicMock',
  'from gameserver.network.rest_api import create_app',
  'services = MagicMock()',
  'services.bot_detector = None',
  'app = create_app(services)',
  'print(json.dumps(app.openapi()))',
].join('\n');

// Write script to a temp file to avoid shell quoting issues
import { mkdtempSync, writeFileSync as wfs, rmSync } from 'fs';
const tmpDir = mkdtempSync(`${tmpdir()}/gen-openapi-`);
const scriptPath = `${tmpDir}/gen.py`;
wfs(scriptPath, script);

try {
  const env = { ...process.env, JWT_SECRET: 'placeholder-for-schema-generation' }; // pragma: allowlist secret
  const raw = execFileSync(python, ['-W', 'ignore', scriptPath], { cwd: repoRoot, encoding: 'utf8', env, stdio: ['pipe', 'pipe', 'inherit'] });
  // structlog may write to stdout — grab only the last line which is the JSON
  const jsonLine = raw.trim().split('\n').at(-1);
  const schema = JSON.parse(jsonLine);
  writeFileSync(outPath, JSON.stringify(schema, null, 2));
  console.log(`wrote ${outPath} (${Object.keys(schema.paths).length} paths)`);
} finally {
  rmSync(tmpDir, { recursive: true });
}
