#!/usr/bin/env node
/**
 * Local grouping evaluator — runs the REAL frontend grouping logic against
 * span data extracted by scripts/dump-pdf-spans.py.
 *
 * Local-only: reads JSON from a directory (default /tmp/pdf-eval), never
 * uploads anything. Run with Node ≥22.6 (native TS support):
 *
 *   node scripts/eval-grouping.ts /tmp/pdf-eval [--fonts]
 *
 * The spans JSON shape matches /api/pdf/{id}/structure, so this validates the
 * exact same code path the sidebar uses (grouping.ts), offline.
 */

import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { groupElements } from '../frontend/src/lib/utils/grouping.ts';

const dir = process.argv[2] ?? '/tmp/pdf-eval';
const showFonts = process.argv.includes('--fonts');

let failed = 0;
for (const file of readdirSync(dir).filter(f => f.endsWith('.json')).sort()) {
	const data = JSON.parse(readFileSync(join(dir, file), 'utf-8'));
	console.log(`\n=== ${file} ===`);
	for (const page of data.pages as Array<{ page: number; elements: any[] }>) {
		const groups = groupElements(page.elements as any);
		const lines = groups.map(g => {
			const suffix = showFonts ? `  [${g.font} ${g.size}pt]` : '';
			return `    "${g.text}"${suffix}`;
		});
		console.log(`  page ${page.page} (${page.elements.length} spans -> ${groups.length} groups):`);
		console.log(lines.join('\n'));
	}
}
console.log(`\ndone — ${failed} failures`);
process.exit(failed > 0 ? 1 : 0);
