// Optional documentation tool; Marked is supplied externally, not a TPV dependency.
import { readFileSync } from 'node:fs';
import { isAbsolute } from 'node:path';
import { pathToFileURL } from 'node:url';

const modulePath = process.argv[2] || 'marked';
const source = isAbsolute(modulePath) ? pathToFileURL(modulePath).href : modulePath;
const { marked } = await import(source);
const documents = JSON.parse(readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(documents.map(d => ({
  path: d.path,
  html: marked.parse(d.markdown, { gfm: true, breaks: false })
}))));
