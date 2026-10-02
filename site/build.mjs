import { mkdir, copyFile, cp, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const site = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(site);
const output = path.join(site, 'public');
await mkdir(output, { recursive: true });
for (const file of ['index.html', 'app.js', 'style.css']) {
  await copyFile(path.join(site, file), path.join(output, file));
}
await cp(path.join(root, 'studio/themes'), path.join(output, 'themes'), { recursive: true });
await cp(path.join(root, 'previews/characters'), path.join(output, 'characters'), { recursive: true });

const packs = [
  ['reze', '蕾塞光标-Windows-V1.5.zip', 'reze-windows-v1.5.zip', 'V1.5'],
  ['rem', 'RemCursor-Windows-v1.2.1.zip', 'rem-windows-v1.2.1.zip', 'V1.2.1'],
  ['deepseek', 'deepseek酱光标-样本-V1.5.zip', 'deepseek-windows-v1.5.zip', 'V1.5'],
  ['pochita', 'Pochita-Mini光标-V1.5.zip', 'pochita-mini-windows-v1.5.zip', 'V1.5'],
  ['pinkhorn', 'ZeroTwo-Q版光标-Windows-V1.5.zip', 'zero-two-windows-v1.5.zip', 'V1.5'],
  ['studio', '角色光标工作台-WebUI-V1.1.1.zip', 'character-cursor-studio-v1.1.1.zip', 'V1.1.1']
];
await mkdir(path.join(output, 'downloads'), { recursive: true });
const downloads = {};
const release = JSON.parse(await readFile(path.join(root, 'release/version.json'), 'utf8'));
const fullFilename = `角色光标完整合集-V${release.version}.zip`;
const fullRelease = {version: release.version,
  url: `https://github.com/jinhongsop-ux/codex-character-cursors/releases/latest/download/${encodeURIComponent(fullFilename)}`,
  filename: fullFilename};
for (const [id, filename, published, version] of packs) {
  const data = await readFile(path.join(root, 'packs', filename));
  await copyFile(path.join(root, 'packs', filename), path.join(output, 'downloads', published));
  downloads[id] = { url: `/downloads/${published}`, filename, version, bytes: data.length,
    sha256: createHash('sha256').update(data).digest('hex') };
}
const themes = JSON.parse((await readFile(path.join(root, 'studio/themes/catalog.json'), 'utf8')).replace(/^\uFEFF/, ''));
await writeFile(path.join(output, 'catalog.json'), JSON.stringify({ themes, downloads, fullRelease }));
await writeFile(path.join(output, 'downloads/SHA256SUMS.txt'), Object.values(downloads)
  .map(d => `${d.sha256}  ${d.url.split('/').pop()}`).join('\n') + '\n');
console.log(`Built public preview: ${themes.length} characters, ${packs.length} original ZIP downloads.`);
