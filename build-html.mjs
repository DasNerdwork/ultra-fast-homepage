// Injiziert das gebaute Tailwind-CSS inline ins HTML, um den
// render-blockierenden CSS-Request zu eliminieren (LCP)
import { readFileSync, writeFileSync } from 'node:fs';

const MARKER = '/* INLINE_CSS */';

const css = readFileSync('./static/assets/css/output.css', 'utf8');
const template = readFileSync('./index.template.html', 'utf8');

if (!template.includes(MARKER)) {
    console.error(`FEHLER: Marker "${MARKER}" nicht in index.template.html gefunden, breche ab.`);
    process.exit(1);
}

// Replacer-Funktion statt String, damit $-Zeichen im CSS
// nicht als Replace-Pattern interpretiert werden
const html = template.replace(MARKER, () => css);

writeFileSync('./static/index.html', html);
console.log(`index.html gebaut, ${(css.length / 1024).toFixed(1)} KiB CSS inlined`);