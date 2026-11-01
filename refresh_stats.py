"""Refresh public GitHub stats with gh CLI. No credentials are written to disk."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import subprocess, json, html, re

ROOT = Path(__file__).resolve().parent
LOGIN = 'imafreakandyalldontknowit67'
def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True, encoding='utf-8'))

profile = api('users/' + LOGIN)
repos = []
page = 1
while True:
    batch = api(f'users/{LOGIN}/repos?per_page=100&page={page}')
    repos.extend(batch)
    if len(batch) < 100: break
    page += 1
owned = [r for r in repos if not r['fork'] and r['name'].lower() != LOGIN.lower()]
languages = Counter()
for repo in owned:
    languages.update(api(f'repos/{LOGIN}/{repo["name"]}/languages'))
total = sum(languages.values())
stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
snapshot = {'updated': stamp, 'public_repos': len(repos), 'non_fork_repos': len(owned),
            'stars': sum(r['stargazers_count'] for r in repos),
            'followers': profile['followers'], 'language_bytes_non_fork': dict(languages)}
(ROOT / 'stats-data.json').write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
palette = json.loads((ROOT / 'palette.json').read_text(encoding='utf-8'))
height = max(190, 104 + min(len(languages), 4) * 30)
for theme in ('dark', 'light'):
    c = palette[theme]
    lines = []
    for i, (language, count) in enumerate(languages.most_common(4)):
        y = 77 + i * 30
        pct = count / total * 100
        lines.append(f'<text x="488" y="{y}" fill="{c["text"]}" font-size="14">{html.escape(language)}</text>')
        lines.append(f'<rect x="628" y="{y-10}" width="150" height="6" rx="3" fill="{c["border"]}"/>')
        lines.append(f'<rect x="628" y="{y-10}" width="{150*pct/100:.2f}" height="6" rx="3" fill="{c["accent"]}"/>')
        lines.append(f'<text x="850" y="{y}" text-anchor="end" fill="{c["muted"]}" font-size="13">{pct:.1f}%</text>')
    if not languages:
        lines.append(f'<text x="488" y="77" fill="{c["muted"]}" font-size="14">No public language data yet.</text>')
    metric = []
    for x, value, label in [(40,len(repos),'public repos'),(177,snapshot['stars'],'stars'),(310,profile['followers'],'followers')]:
        metric.append(f'<text x="{x}" y="96" fill="{c["text"]}" font-size="32">{value}</text><text x="{x}" y="124" fill="{c["muted"]}" font-size="12">{label}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">
<defs><linearGradient id="glass"><stop stop-color="{c['background']}"/><stop offset="1" stop-color="{c['border']}"/></linearGradient></defs>
<rect width="900" height="{height}" rx="5" fill="{c['background']}"/>
<rect x="12" y="12" width="876" height="{height-24}" rx="5" fill="url(#glass)"/>
<rect x="12" y="12" width="876" height="{height-24}" rx="5" fill="{c['background']}" fill-opacity=".58" stroke="{c['border']}"/>
<path d="M450 38V{height-54}" stroke="{c['border']}"/>
<g font-family="Consolas,monospace">
<text x="40" y="46" font-size="12" letter-spacing="2" fill="{c['accent']}">PROFILE</text>
<text x="488" y="46" font-size="12" letter-spacing="2" fill="{c['accent']}">TOP LANGUAGES</text>
{''.join(metric)}{''.join(lines)}
<text x="40" y="{height-30}" font-size="11" fill="{c['muted']}">Updated {stamp}</text>
</g></svg>'''
    (ROOT / 'assets' / f'stats-{theme}.svg').write_text(svg, encoding='utf-8')

lang_alt = ', '.join(f'{lang} {n/total:.1%}' for lang,n in languages.most_common(4)) or 'No data'
alt = html.escape(f'Public GitHub snapshot: {len(repos)} repositories, {snapshot["stars"]} stars including forks, {profile["followers"]} followers. Languages by code bytes, excluding forks: {lang_alt}. Updated {stamp}.', quote=True)
block = f'''<!-- stats:start -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/stats-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/stats-light.svg">
  <img src="assets/stats-dark.svg" width="900" alt="{alt}">
</picture>
<!-- stats:end -->'''
for filename in ('README.md', 'index.html'):
    file = ROOT / filename
    if not file.exists():
        continue  # The local preview is deliberately not published.
    s = file.read_text(encoding='utf-8')
    if '<!-- stats:start -->' in s:
        s = re.sub(r'<!-- stats:start -->.*?<!-- stats:end -->',lambda _:block,s,flags=re.S)
    else:
        marker = '### projects' if filename.endswith('.md') else '<h3>projects</h3>'
        s = s.replace(marker, block + '\n\n' + marker, 1)
    file.write_text(s,encoding='utf-8')
from activity_panel import refresh
refresh(ROOT, LOGIN, owned, api, stamp, palette)
file = ROOT / 'index.html'
if file.exists():
    s = file.read_text(encoding='utf-8')
    md = (ROOT / 'README.md').read_text(encoding='utf-8')
    s = re.sub(r'(<textarea[^>]+id="sourceText"[^>]*>).*?(</textarea>)',lambda m:m[1]+html.escape(md)+m[2],s,flags=re.S)
    file.write_text(s,encoding='utf-8')
print(json.dumps(snapshot, indent=2))
