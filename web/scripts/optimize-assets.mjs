/**
 * Asset optimisation: convert JPG/PNG sprites to WebP siblings.
 *
 * Skips PWA icons (apple-touch-icon, icon-192, icon-512) because browsers
 * require PNG for those. Also skips files that already have a same-name .webp.
 *
 * Usage:
 *   node scripts/optimize-assets.mjs            # dry-run (shows plan)
 *   node scripts/optimize-assets.mjs --write    # convert and write files
 */

import sharp from 'sharp';
import { readdir, stat } from 'fs/promises';
import { join, extname, basename, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS_DIR = join(__dirname, '..', 'assets');
const DRY_RUN = !process.argv.includes('--write');

// PWA icons must stay PNG — browsers don't accept WebP for manifest icons
const SKIP_NAMES = new Set([
  'apple-touch-icon.png',
  'icon-192.png',
  'icon-512.png',
]);

async function* walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(fullPath);
    } else {
      yield fullPath;
    }
  }
}

async function main() {
  const targets = [];

  for await (const filePath of walk(ASSETS_DIR)) {
    const ext = extname(filePath).toLowerCase();
    if (ext !== '.jpg' && ext !== '.jpeg' && ext !== '.png') continue;
    if (SKIP_NAMES.has(basename(filePath))) continue;

    const webpPath = filePath.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    if (existsSync(webpPath)) {
      // Already converted — still report size comparison
      const origSize = (await stat(filePath)).size;
      const webpSize = (await stat(webpPath)).size;
      const saving = Math.round((1 - webpSize / origSize) * 100);
      console.log(`  [skip]   ${basename(filePath)} → already exists (${saving}% smaller)`);
      continue;
    }

    targets.push({ src: filePath, dest: webpPath });
  }

  if (targets.length === 0) {
    console.log('No new files to convert.');
    return;
  }

  console.log(`\n${DRY_RUN ? '[DRY RUN] ' : ''}Converting ${targets.length} file(s) to WebP:\n`);

  let totalSaved = 0;
  for (const { src, dest } of targets) {
    const origSize = (await stat(src)).size;

    if (DRY_RUN) {
      console.log(`  ${basename(src)} → ${basename(dest)}`);
      continue;
    }

    const ext = extname(src).toLowerCase();
    let pipeline = sharp(src);

    // JPEGs: quality 82 balances size vs visual fidelity for photos
    // PNGs:  lossless=false, quality 85 — good for sprites with transparency
    if (ext === '.jpg' || ext === '.jpeg') {
      pipeline = pipeline.webp({ quality: 82 });
    } else {
      pipeline = pipeline.webp({ quality: 85, lossless: false });
    }

    await pipeline.toFile(dest);
    const webpSize = (await stat(dest)).size;

    // Don't keep WebP if it's larger than the source (common for small sprites)
    if (webpSize >= origSize) {
      const { unlink } = await import('fs/promises');
      await unlink(dest);
      console.log(`  [skip]   ${basename(src).padEnd(40)} WebP larger — keeping original`);
      continue;
    }

    const saved = origSize - webpSize;
    totalSaved += saved;
    const pct = Math.round((1 - webpSize / origSize) * 100);
    console.log(`  ✓ ${basename(src).padEnd(40)} ${(origSize/1024).toFixed(1).padStart(6)} kB → ${(webpSize/1024).toFixed(1).padStart(6)} kB  (${pct}% saved)`);
  }

  if (!DRY_RUN && totalSaved > 0) {
    console.log(`\nTotal saved: ${(totalSaved / 1024).toFixed(0)} kB`);
  }

  if (DRY_RUN) {
    console.log('\nRun with --write to apply conversions.');
  }
}

main().catch(err => { console.error(err); process.exit(1); });
