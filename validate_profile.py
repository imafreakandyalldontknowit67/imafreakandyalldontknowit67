"""Offline checks shared by the publish process and daily GitHub Action."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
README = (ROOT / 'README.md').read_text(encoding='utf-8')

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []
        self.picture_depth = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in {'script', 'iframe', 'object', 'embed', 'style'}, tag
        if tag == 'picture': self.picture_depth += 1
        if tag in {'img', 'source'}:
            assert self.picture_depth == 1
            src = attrs.get('src') or attrs.get('srcset')
            assert src and src.startswith('assets/') and '..' not in src
            assert (ROOT / src).is_file(), src
            self.images.append(src)
            if tag == 'img': assert attrs.get('alt'), src
        if tag == 'a':
            href = attrs.get('href', '')
            assert href.startswith('https://github.com/imafreakandyalldontknowit67'), href
            self.links.append(href)
    def handle_endtag(self, tag):
        if tag == 'picture': self.picture_depth -= 1

parsed = Images(); parsed.feed(README)
assert parsed.picture_depth == 0
assert len(set(parsed.images)) >= 6
for name in set(parsed.images):
    path = ROOT / name
    assert path.stat().st_size < 1_000_000, name
    if path.suffix == '.svg':
        tree = ET.parse(path)
        for node in tree.iter():
            assert node.tag.split('}')[-1] not in {'script', 'foreignObject', 'image'}
            assert not any(k.lower().startswith('on') for k in node.attrib)
    if path.suffix == '.gif': assert path.read_bytes()[:6] in {b'GIF87a', b'GIF89a'}
for key in ('stats', 'activity'):
    assert README.count(f'<!-- {key}:start -->') == 1
    assert README.count(f'<!-- {key}:end -->') == 1
assert '### projects' in README and '### recent activity' in README
assert not re.search(r'spotifast|CAT ONLINE|/dev/me|source-dark.svg|releases-dark.svg', README, re.I)
stats = json.loads((ROOT / 'stats-data.json').read_text(encoding='utf-8'))
activity = json.loads((ROOT / 'activity-data.json').read_text(encoding='utf-8'))
assert len(activity['entries']) <= 3
assert all(x['repo'] != 'imafreakandyalldontknowit67' for x in activity['entries'])
assert stats['updated'] in README
print(f'Validated {len(set(parsed.images))} assets, {len(parsed.links)} links, SVG safety, metadata, and README structure.')
