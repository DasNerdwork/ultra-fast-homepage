// Injiziert das gebaute Tailwind-CSS UND das Flowbite-CSS inline ins HTML.
// Reihenfolge wichtig: output.css zuerst, flowbite.min.css danach —
// identisch zur früheren <link>-Reihenfolge, damit die Cascade und
// damit das finale Aussehen exakt gleich bleiben.
import { readFileSync, writeFileSync } from 'node:fs';

const MARKER = '/* INLINE_CSS */';

const outputCss = readFileSync('./static/assets/css/output.css', 'utf8');
const flowbiteCss = readFileSync('./static/assets/css/flowbite.min.css', 'utf8');
const template = readFileSync('./index.template.html', 'utf8');

if (!template.includes(MARKER)) {
    console.error(`FEHLER: Marker "${MARKER}" nicht in index.template.html gefunden, breche ab.`);
    process.exit(1);
}

const css = outputCss + '\n' + flowbiteCss;
const html = template.replace(MARKER, () => css);

writeFileSync('./static/index.html', html);
console.log(`index.html gebaut, ${(css.length / 1024).toFixed(1)} KiB CSS inlined (output + flowbite)`);