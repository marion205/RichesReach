#!/usr/bin/env node
/**
 * wire-envs.js
 * - Rewrites hardcoded URLs to env-driven values
 * - Generates environment_template.env (+ optionally seeds mobile/.env)
 * - Prints ripgrep commands to find any missed URLs/envs
 *
 * Usage:
 *   node scripts/wire-envs.js --dry-run     # preview only
 *   node scripts/wire-envs.js --apply       # make changes
 */
const fs = require('fs');
const path = require('path');

const APPLY = process.argv.includes('--apply');
const DRY = process.argv.includes('--dry-run') || !APPLY;
const REPO_ROOT = process.cwd();
const MOBILE_DIR = path.join(REPO_ROOT, 'mobile');
const BACKEND_DIR = path.join(REPO_ROOT, 'backend');
const FILE_EXTS = ['.ts', '.tsx', '.js', '.jsx', '.json', '.py', '.yaml', '.yml', '.env', '.gradle', '.swift', '.m', '.mm'];
const IGNORE_DIRS = new Set([
  'node_modules', '.git', 'build', 'dist', 'Pods', '.expo', '.expo-shared',
  '.turbo', '.next', '.cache', 'android', 'ios/DerivedData'
]);

// Replacement rules (ordered)
const RULES = [
  {
    label: 'Map ws://localhost:8000/ws/ → EXPO_PUBLIC_WS_URL || WS_URL',
    re: /\b(wss?:\/\/)(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?\/ws\/?/g,
    repl: (_m, _proto, _host, _port) => '${process.env.EXPO_PUBLIC_WS_URL || process.env.WS_URL}',
    files: ['.ts', '.tsx', '.js', '.jsx']
  },
  {
    label: 'Map ws(s)://localhost[:port] → EXPO_PUBLIC_SIGNAL_URL',
    re: /\b(wss?:\/\/)(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?(\/socket\.io)?\b/g,
    repl: () => 'process.env.EXPO_PUBLIC_SIGNAL_URL',
    files: ['.ts', '.tsx', '.js', '.jsx']
  },
  {
    label: 'Map http(s)://localhost[:port] → EXPO_PUBLIC_API_BASE_URL || API_BASE_URL',
    re: /\b(https?:\/\/)(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?\b(?!\/socket\.io)/g,
    repl: () => '${process.env.EXPO_PUBLIC_API_BASE_URL || process.env.API_BASE_URL}',
    files: ['.ts', '.tsx', '.js', '.jsx']
  },
  {
    label: 'JSON: ws preview to EXPO_PUBLIC_WS_URL',
    re: /"ws(s)?:\/\/(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?\/ws\/?"/g,
    repl: () => '"${EXPO_PUBLIC_WS_URL}"',
    files: ['.json']
  },
  {
    label: 'JSON: ws signaling to EXPO_PUBLIC_SIGNAL_URL',
    re: /"ws(s)?:\/\/(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?(\/socket\.io)?"/g,
    repl: () => '"${EXPO_PUBLIC_SIGNAL_URL}"',
    files: ['.json']
  },
  {
    label: 'Python: http localhost → API_BASE_URL',
    re: /\b(https?:\/\/)(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?\b/g,
    repl: () => 'os.getenv("API_BASE_URL", "http://localhost:8000")',
    files: ['.py']
  },
];

const ENV_TEMPLATE = `# ==== MOBILE / FRONTEND ================================================
# GraphQL / REST base
EXPO_PUBLIC_API_BASE_URL=https://api.YOURDOMAIN.com

# WebSocket: screen-level “preview room”
EXPO_PUBLIC_WS_URL=wss://api.YOURDOMAIN.com/ws/

# Signaling server (Socket.IO over secure WebSocket)
EXPO_PUBLIC_SIGNAL_URL=wss://signal.YOURDOMAIN.com/socket.io

# TURN / ICE
# Comma-separated list; e.g.:
# stun:turn.YOURDOMAIN.com:3478,turn:turn.YOURDOMAIN.com:3478?transport=udp,turn:turn.YOURDOMAIN.com:3478?transport=tcp,turns:turn.YOURDOMAIN.com:5349?transport=tcp
EXPO_PUBLIC_TURN_URLS=stun:stun.l.google.com:19302
EXPO_PUBLIC_TURN_USERNAME=
EXPO_PUBLIC_TURN_CREDENTIAL=

# ==== BACKEND / SERVER ================================================
API_BASE_URL=https://api.YOURDOMAIN.com
SIGNAL_URL=wss://signal.YOURDOMAIN.com/socket.io
TURN_URLS=stun:stun.l.google.com:19302
TURN_USERNAME=
TURN_CREDENTIAL=
# Authorization: Bearer <JWT>
`;

function walk(dir, out = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    if (IGNORE_DIRS.has(e.name)) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

function shouldTouch(file) {
  const ext = path.extname(file);
  if (!FILE_EXTS.includes(ext)) return false;
  const base = path.basename(file);
  if (/^(package-lock|yarn\.lock|pnpm-lock|Podfile\.lock)$/i.test(base)) return false;
  if (base.endsWith('.min.js')) return false;
  return true;
}

function applyRulesToFile(file) {
  const ext = path.extname(file);
  let content = fs.readFileSync(file, 'utf8');
  let updated = content;
  let touched = false;
  for (const rule of RULES) {
    if (!rule.files.includes(ext)) continue;
    const before = updated;
    updated = updated.replace(rule.re, rule.repl);
    if (updated !== before) {
      touched = true;
      console.log(`• ${rule.label}\n  → ${path.relative(REPO_ROOT, file)}`);
    }
  }
  if (touched && !DRY) fs.writeFileSync(file, updated, 'utf8');
  return touched;
}

console.log(`\n[wire-envs] ${DRY ? 'DRY RUN (no writes)' : 'APPLYING CHANGES'}\n`);
const files = walk(REPO_ROOT).filter(shouldTouch);
let changed = 0;
for (const f of files) {
  if (applyRulesToFile(f)) changed++;
}
console.log(`\n[wire-envs] Touched files: ${changed}`);

const templatePath = path.join(REPO_ROOT, 'environment_template.env');
if (DRY) {
  console.log(`\n[wire-envs] Would write: ${path.relative(REPO_ROOT, templatePath)} (skipped in dry-run)`);
} else {
  fs.writeFileSync(templatePath, ENV_TEMPLATE, 'utf8');
  console.log(`[wire-envs] Wrote ${path.relative(REPO_ROOT, templatePath)}`);
}

const mobileEnv = path.join(MOBILE_DIR, '.env');
if (!fs.existsSync(MOBILE_DIR)) {
  console.warn('[wire-envs] mobile/ not found – skipping mobile/.env seed');
} else if (fs.existsSync(mobileEnv)) {
  console.log('[wire-envs] mobile/.env already exists (left untouched)');
} else if (!DRY) {
  fs.writeFileSync(mobileEnv, ENV_TEMPLATE, 'utf8');
  console.log('[wire-envs] Seeded mobile/.env (copy this into real values)');
} else {
  console.log('[wire-envs] Would seed mobile/.env (skipped in dry-run)');
}

console.log(`\n[wire-envs] Next steps:
  1) Review changes (git diff) and fill values in:
     - environment_template.env
     - mobile/.env (copied above)
  2) Find any remaining hardcoded URLs / missing envs with:
     rg -n "(http|ws)s?://[A-Za-z0-9.:-/]+"
     rg -n "localhost:|127\\.0\\.0\\.1|192\\.168\\."
     rg -n "(EXPO_PUBLIC_|WS_URL|SIGNAL|GRAPHQL|API|BASE_URL|TURN|ICE|WALLETCONNECT|ALCHEMY|STREAM_API_KEY)"
  3) Restart the app:
     cd mobile
     expo start --clear
`);


