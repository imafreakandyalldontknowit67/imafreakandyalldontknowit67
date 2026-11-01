"""Public non-fork project activity; invoked by refresh_stats.py."""
from pathlib import Path
import html, json, re

def refresh(root, login, repos, api, stamp, palette):
    allowed = {r['full_name'] for r in repos}
    entries = []
    events = api(f'users/{login}/events/public?per_page=100')
    verbs = {'PushEvent': 'Pushed updates', 'PublicEvent': 'Made repository public',
             'CreateEvent': 'Created', 'PullRequestEvent': 'Updated pull request',
             'IssuesEvent': 'Updated issue'}
    for event in events:
        repo = event['repo']['name']
        if repo not in allowed or event['type'] not in verbs:
            continue
        payload = event.get('payload', {})
        label = verbs[event['type']]
        if event['type'] == 'CreateEvent': label += ' ' + payload.get('ref_type', 'reference')
        entries.append({'date': event['created_at'], 'repo': repo.split('/')[-1],
                        'label': label, 'url': 'https://github.com/' + repo})
    for repo in repos:
        for release in api(f'repos/{repo["full_name"]}/releases?per_page=3'):
            if release.get('draft') or not release.get('published_at'): continue
            entries.append({'date': release['published_at'], 'repo': repo['name'],
                'label': 'Released ' + release['tag_name'], 'url': release['html_url']})
    entries.sort(key=lambda row: row['date'], reverse=True)
    entries = entries[:3]
    (root/'activity-data.json').write_text(json.dumps({'updated':stamp,'entries':entries},indent=2),encoding='utf-8')
    # Each row is a separate linked image, so every entry is independently clickable.
    markup = []
    for i, entry in enumerate(entries):
        alt = html.escape(f'{entry["date"][:10]}: {entry["repo"]} — {entry["label"]}',quote=True)
        for theme in ('dark','light'):
            c = palette[theme]
            label = entry['label'] if len(entry['label']) <= 45 else entry['label'][:42]+'...'
            name = entry['repo'] if len(entry['repo']) <= 30 else entry['repo'][:27]+'...'
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="76" viewBox="0 0 900 76">
<defs><linearGradient id="glass"><stop stop-color="{c['background']}"/><stop offset="1" stop-color="{c['border']}"/></linearGradient></defs>
<rect x="12" y="4" width="876" height="68" rx="4" fill="url(#glass)"/>
<rect x="12" y="4" width="876" height="68" rx="4" fill="{c['background']}" fill-opacity=".58" stroke="{c['border']}"/>
<g font-family="Consolas,monospace"><text x="36" y="43" font-size="13" fill="{c['muted']}">{entry['date'][:10]}</text>
<text x="174" y="31" font-size="14" fill="{c['accent']}">{html.escape(name)}</text>
<text x="174" y="53" font-size="13" fill="{c['text']}">{html.escape(label)}</text></g></svg>'''
            (root/'assets'/f'activity-{i}-{theme}.svg').write_text(svg,encoding='utf-8')
        markup.append(f'''<a href="{html.escape(entry['url'],quote=True)}">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/activity-{i}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/activity-{i}-light.svg">
  <img src="assets/activity-{i}-dark.svg" width="900" alt="{alt}">
</picture>
</a>''')
    rows = '\n\n'.join(markup) if markup else '<p>No recent public project activity available.</p>'
    for filename, heading, end in [('README.md','### recent activity','\n---'),('index.html','<h3>recent activity</h3>','<hr>')]:
        path=root/filename
        if not path.exists():
            continue
        s=path.read_text(encoding='utf-8')
        block='<!-- activity:start -->\n\n'+heading+'\n\n'+rows+'\n\n<!-- activity:end -->'
        if '<!-- activity:start -->' in s:
            s=re.sub(r'<!-- activity:start -->.*?<!-- activity:end -->',lambda _:block,s,flags=re.S)
        else:
            s=s.replace(end,'\n\n'+block+'\n\n'+end,1)
        s = s.replace('</a>\n<!-- activity:start -->', '</a>\n\n<!-- activity:start -->')
        path.write_text(s,encoding='utf-8')
    print(f'Refreshed {len(entries)} public project activity entries.')
