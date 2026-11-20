"""Instagram投稿（etoi-images/posts/NN）からウェブ記事のデータと画像を作る。
usage: python3 tools/import_post.py <etoi-images/posts/NN> <元画像フォルダ（d.jpg 等）>
出力: content/NN.json, static/img/NN/hero.jpg, sNN.jpg（各スライドの細部）, og.jpg
meta/NN.json（slug, theme, lead）が必要。事実は投稿の文面・キャプションのみを使い、新しく足さない。"""
import sys, os, re, json, runpy
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
post, srcdir = sys.argv[1], sys.argv[2]
no = os.path.basename(os.path.normpath(post))
cfg = runpy.run_path(os.path.join(post, 'cfg.py'))
meta = json.load(open(os.path.join(ROOT, 'meta', no + '.json'), encoding='utf-8'))
cap = cfg['CAPTION'].strip()
out_img = os.path.join(ROOT, 'static', 'img', no); os.makedirs(out_img, exist_ok=True)
SRC = {k: Image.open(os.path.join(srcdir, k + '.jpg')).convert('RGB') for k in cfg['IMAGES']}
W, H = 1080, 1350

def view(k, c):
    im = SRC[k]; iw, ih = im.size; cx, cy, h = c; vh = h * ih; vw = vh * W / H
    if vw > iw or vh > ih:  # 全体を見せる
        s = min(1600 / iw, 1600 / ih, 1); return im.resize((int(iw * s), int(ih * s)), Image.LANCZOS), True
    px = min(max(cx * iw, vw / 2), iw - vw / 2); py = min(max(cy * ih, vh / 2), ih - vh / 2)
    return im.crop((int(px - vw / 2), int(py - vh / 2), int(px + vw / 2), int(py + vh / 2))).resize((W, H), Image.LANCZOS), False

# --- キャプションの分解 ---
lines = cap.splitlines()
title_line = lines[0].lstrip('🎨').strip()
m = re.match(r'(.+?)（(.+)）$', title_line)
title_ja, title_orig = (m.group(1), m.group(2)) if m else (title_line, '')
artist_line = lines[1].lstrip('—').strip()
m = re.match(r'(.+?)（(.+)）$', artist_line)
artist_ja, artist_orig = (m.group(1), m.group(2)) if m else (artist_line, '')
medium = lines[2].strip()
museum = lines[3].lstrip('📍').strip()
sections, credit, sources, tags = [], '', '', []
cur = None
for ln in lines[4:]:
    s = ln.strip()
    mm = re.match(r'^([1-9])️⃣\s*(.+)$', s)
    if mm: cur = {'h': mm.group(2), 'p': []}; sections.append(cur); continue
    if s.startswith('出典：'): sources = s[3:]; cur = None; continue
    if s.startswith('画像：'): credit = s[3:]; cur = None; continue
    if s.startswith('#'): tags = [t.lstrip('#') for t in s.split() if t.startswith('#')]; continue
    if cur is not None and s: cur['p'].append(s)

slides = []
for i, sl in enumerate(cfg['SLIDES']):
    if sl.get('mock'): continue
    im, full = view(sl.get('img', 'd'), sl['cam'])
    fn = 's%02d.jpg' % (i + 1)
    im.save(os.path.join(out_img, fn), quality=80, optimize=True, progressive=True)
    slides.append({'img': fn, 'full': full, 't': sl['t']})

d = SRC['d']; s = min(1800 / d.width, 1800 / d.height, 1)
d.resize((int(d.width * s), int(d.height * s)), Image.LANCZOS).save(os.path.join(out_img, 'hero.jpg'), quality=82, optimize=True, progressive=True)
# OGP 1200x630
r = max(1200 / d.width, 630 / d.height); og = d.resize((int(d.width * r) + 1, int(d.height * r) + 1), Image.LANCZOS)
og.crop(((og.width - 1200) // 2, (og.height - 630) // 2, (og.width - 1200) // 2 + 1200, (og.height - 630) // 2 + 630)).save(os.path.join(out_img, 'og.jpg'), quality=80)
th = d.copy(); th.thumbnail((800, 800)); th.save(os.path.join(out_img, 'thumb.jpg'), quality=78, optimize=True)

data = dict(meta, no=no, title_ja=title_ja, title_orig=title_orig, artist_ja=artist_ja, artist_orig=artist_orig,
            medium=medium, museum=museum, slides=slides, sections=sections, sources=sources, credit=credit, tags=tags,
            hook=''.join(slides[0]['t']), final=''.join(slides[-1]['t']))
os.makedirs(os.path.join(ROOT, 'content'), exist_ok=True)
json.dump(data, open(os.path.join(ROOT, 'content', no + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', no, title_ja, len(slides), 'slides')
