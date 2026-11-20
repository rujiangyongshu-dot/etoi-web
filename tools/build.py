"""content/*.json からサイト全体を docs/ に書き出す（GitHub Pages は docs/ を公開）。
usage: python3 tools/build.py [--root-relative]   （--root-relative はプレビュー用に相対パスで書き出す）"""
import os, sys, json, glob, shutil, datetime, html
from jinja2 import Environment, FileSystemLoader
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'docs')
REL = '--root-relative' in sys.argv
site = json.load(open(os.path.join(R, 'site.json'), encoding='utf-8'))
themes = json.load(open(os.path.join(R, 'themes.json'), encoding='utf-8'))
tmap = {t['key']: t for t in themes}
works = [json.load(open(p, encoding='utf-8')) for p in glob.glob(os.path.join(R, 'content', '*.json'))]
works = [w for w in works if not w.get('draft')]
works.sort(key=lambda w: (w.get('published', ''), w['no']), reverse=True)
for w in works:
    w['theme_name'] = tmap[w['theme']]['name']
    im = Image.open(os.path.join(R, 'static', 'img', w['no'], 'hero.jpg')); w['hero_w'], w['hero_h'] = im.size
for t in themes: t['works'] = [w for w in works if w['theme'] == t['key']]
env = Environment(loader=FileSystemLoader(os.path.join(R, 'templates')), autoescape=True)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
ver = now.strftime('%Y%m%d%H%M')
if os.path.isdir(OUT):
    for x in os.listdir(OUT):
        if x in ('CNAME', '.nojekyll'): continue
        p = os.path.join(OUT, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, '.nojekyll'), 'w').close()
shutil.copytree(os.path.join(R, 'static'), os.path.join(OUT, 'static'), dirs_exist_ok=True)
urls = []

def page(path, tpl, **kw):
    depth = path.strip('/').count('/') + (1 if path.strip('/') else 0)
    root = ('../' * depth) if REL else site.get('base_path', '/')
    if REL and not root: root = './'
    ctx = dict(idx='index.html' if REL else '', site=site, path=path, root=root, year=now.year, ver=ver, themes=themes, works=works)
    ctx.update(kw)
    s = env.get_template(tpl).render(**ctx)
    if REL:
        import re
        s = re.sub(r'href="((?:\.\./|\./)[^"#?]*?/)?"', lambda m: 'href="%sindex.html"' % (m.group(1) or './'), s)
    d = os.path.join(OUT, path.strip('/')); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(s)
    urls.append(path)

D = site['description']
page('/', 'index.html', title='ETOI（エトワ）｜名画を、仕事と人生の言葉で読み解く', desc=D, feature=works[0])
page('/works/', 'list.html', title='名画の読み解き一覧｜ETOI', desc=D, h1='読み解き一覧', kicker='ALL WORKS',
     lead='一枚ずつ、画家の人生と、いまの私たちの悩みを重ねて読み解いています。', items=works)
page('/themes/', 'list.html', title='悩みから絵を探す｜ETOI', desc='いまの悩みに近いテーマから、名画の読み解きを探せます。',
     h1='悩みから、絵を探す', kicker='THEMES', lead='いまの自分に近いものを選んでください。', themes_list=themes)
for t in themes:
    page('/themes/%s/' % t['key'], 'list.html', title='%s に見る絵｜ETOI' % t['name'], desc=t['desc'],
         h1=t['name'], kicker='THEME', lead=t['desc'], items=t['works'], cta_label='theme_' + t['key'])
for w in works:
    rel = [x for x in works if x['theme'] == w['theme'] and x is not w]
    rel += [x for x in works if x['theme'] != w['theme'] and x is not w]
    path = '/works/%s/' % w['slug']
    desc = '%s%s ― %s《%s》を、仕事と人生の言葉で読み解きます。' % (w['slides'][0]['t'][0], w['slides'][0]['t'][1], w['artist_ja'], w['title_ja'])
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": w['hook'], "description": desc,
          "image": site['base_url'] + '/static/img/%s/og.jpg' % w['no'], "inLanguage": "ja",
          "author": {"@type": "Organization", "name": site['operator']}, "publisher": {"@type": "Organization", "name": "ETOI"},
          "datePublished": w.get('published', now.strftime('%Y-%m-%d')),
          "about": {"@type": "VisualArtwork", "name": w['title_ja'], "creator": {"@type": "Person", "name": w['artist_ja']}}}
    page(path, 'work.html', title='%s｜%s《%s》｜ETOI' % (w['hook'], w['artist_ja'], w['title_ja']), desc=desc,
         og_type='article', og_image='/static/img/%s/og.jpg' % w['no'], w=w, related=rel[:3],
         ld=json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'))
wj = [{'no': w['no'], 'slug': w['slug'], 'theme': w['theme'], 'hook': w['hook'], 'title': w['title_ja'], 'artist': w['artist_ja']} for w in works]
tj = [{'key': t['key'], 'name': t['name'], 'desc': t['desc']} for t in themes]
page('/shindan/', 'shindan.html', title='いまの自分に響く一枚診断｜ETOI', desc='3つの質問に答えると、いまのあなたに開いてほしい名画が見つかります。',
     works_json=json.dumps(wj, ensure_ascii=False).replace('</', '<\\/'), themes_json=json.dumps(tj, ensure_ascii=False))
for key, h1, cta in [('about', 'ETOIについて', True), ('policy', '編集方針・広告表記', False), ('privacy', 'プライバシーポリシー', False)]:
    body = open(os.path.join(R, 'pages', key + '.html'), encoding='utf-8').read()
    page('/%s/' % key, 'page.html', title='%s｜ETOI' % h1, desc=D, h1=h1, body=body, show_cta=cta)
# sitemap / robots / feed
b = site['base_url']
open(os.path.join(OUT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join('<url><loc>%s%s</loc></url>\n' % (b, u) for u in urls) + '</urlset>\n')
open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % b)
items = ''.join('<item><title>%s</title><link>%s/works/%s/</link><guid>%s/works/%s/</guid><description>%s</description></item>\n' % (
    html.escape(w['hook'] + '｜' + w['title_ja']), b, w['slug'], b, w['slug'], html.escape(w['lead'])) for w in works[:30])
open(os.path.join(OUT, 'feed.xml'), 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>ETOI</title><link>%s/</link><description>%s</description>\n%s</channel></rss>\n' % (b, html.escape(D), items))
if site.get('domain_cname'): open(os.path.join(OUT, 'CNAME'), 'w').write(site['domain_cname'] + '\n')
print('built', len(urls), 'pages,', len(works), 'works')
