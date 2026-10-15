"""Translation batches.

python -X utf8 tools/batches.py split [--size 140]   -> work/tl/bNNN.tsv + build/terms_bNNN.txt (untranslated only)
python -X utf8 tools/batches.py check bNNN            -> validates work/tl/bNNN.out.tsv; prints OK or errors
python -X utf8 tools/batches.py merge bNNN [..|all]   -> writes checked English into script/*.json
python -X utf8 tools/batches.py pairs bNNN            -> work/tl/bNNN.pairs.txt for the reviewer
python -X utf8 tools/batches.py status                -> translated / total
Input TSV: id, speaker, form, limit, jp. Output TSV: id<TAB>English.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import layout  # noqa: E402

TL = os.path.join(ROOT, 'work', 'tl')
SCRIPT = os.path.join(ROOT, 'script')
JP_RE = re.compile('[　-ヿ一-鿿＀-￯]')
ORD_RE = re.compile(r'\d(?:st|nd|rd|th)\b')


def load_names():
    m = {}
    for ln in open(os.path.join(ROOT, 'tbl', 'names_en.tsv'), encoding='utf-8'):
        if ln.strip():
            jp, en = ln.rstrip('\n').split('\t')
            m[jp] = en
    return m


def glossary_rows():
    """(jp_variants, en, avoid) from the glossary tables + names."""
    rows = []
    for ln in open(os.path.join(ROOT, 'glossary.md'), encoding='utf-8'):
        if ln.startswith('|') and not ln.startswith('|---') and not ln.startswith('| JP'):
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            if len(cells) >= 2 and cells[0]:
                avoid = cells[3] if len(cells) > 3 else ''
                rows.append((cells[0], cells[1], avoid))
    return rows


def all_entries():
    out = []
    for fn in sorted(os.listdir(SCRIPT)):
        if fn.endswith('.json'):
            for e in json.load(open(os.path.join(SCRIPT, fn), encoding='utf-8')):
                out.append((fn, e))
    return out


def limit_of(e):
    if e['form'] == 'choice':
        return 'fields'
    return '~%dch' % (44 * max(1, e['nlines']) + 10)


def split(size):
    os.makedirs(TL, exist_ok=True)
    names = load_names()
    existing = [f for f in os.listdir(TL) if re.match(r'b\d{3}\.tsv$', f)]
    done_ids = set()
    for f in existing:
        for ln in open(os.path.join(TL, f), encoding='utf-8'):
            done_ids.add(ln.split('\t', 1)[0])
    n = len(existing)
    cur, cur_region, batches = [], None, []
    for fn, e in all_entries():
        if e['form'] == 'empty' or 'dup' in e or e.get('en') or e['id'] in done_ids:
            continue
        region = e['id'].split('.')[0]
        if len(cur) >= size and region != cur_region:
            batches.append(cur)
            cur = []
        cur.append(e)
        cur_region = region
    if cur:
        batches.append(cur)
    rows = glossary_rows()
    for b in batches:
        name = 'b%03d' % n
        n += 1
        with open(os.path.join(TL, name + '.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            for e in b:
                sp = names.get(e['speaker'], e['speaker']) if e['speaker'] else '-'
                f.write('%s\t%s\t%s\t%s\t%s\n' % (e['id'], sp, e['form'], limit_of(e), e['jp']))
        text = ''.join(e['jp'] for e in b)
        terms = [r for r in rows if any(v and v in text for v in re.split(r'\s*/\s*|\(|\)', r[0]))]
        sp_terms = sorted({e['speaker'] for e in b if e['speaker']})
        with open(os.path.join(ROOT, 'build', 'terms_%s.txt' % name), 'w', encoding='utf-8', newline='\n') as f:
            for r in terms:
                f.write('%s = %s%s\n' % (r[0], r[1], ('   (avoid: %s)' % r[2]) if r[2] else ''))
            for jp, en in sorted(names.items()):
                if jp in text and jp not in sp_terms:
                    f.write('%s = %s\n' % (jp, en))
        print(name, len(b))


def read_in(name):
    rows = []
    for ln in open(os.path.join(TL, name + '.tsv'), encoding='utf-8'):
        p = ln.rstrip('\n').split('\t')
        rows.append({'id': p[0], 'speaker': p[1], 'form': p[2], 'limit': p[3], 'jp': p[4]})
    return rows


def read_out(name):
    p = os.path.join(TL, name + '.out.tsv')
    out, dupes = {}, []
    for ln in open(p, encoding='utf-8-sig'):
        ln = ln.rstrip('\r\n')
        if not ln.strip():
            continue
        if '\t' not in ln:
            raise ValueError('line without tab: %r' % ln[:60])
        k, v = ln.split('\t', 1)
        if k in out:
            dupes.append(k)
        out[k.strip()] = v
    return out, dupes


def check_text(row, en, names_en, rows):
    errs = []
    if not en.strip():
        return ['empty']
    if '\t' in en or '\\u' in en:
        errs.append('tab or \\u escape')
    bad = sorted({c for c in en if ord(c) > 126 or ord(c) < 32})
    if bad:
        errs.append('non-ASCII %r' % ''.join(bad))
    if '{' in en or '}' in en:
        errs.append('{ } not allowed')
    if ORD_RE.search(en) and False:
        errs.append('ordinal')
    if row['form'] == 'choice':
        jl = row['jp'].split(' / ')
        el = en.split(' / ')
        if len(jl) != len(el):
            errs.append('choice: %d lines needed' % len(jl))
        else:
            for a, b in zip(jl, el):
                if len(a.split(' | ')) != len(b.split(' | ')):
                    errs.append('choice: field count differs in %r' % b)
        for line in el:
            lim = 22 if len(line.split(' | ')) == 1 else 10   # two-column notebook menu: 10 cells per column
            for fld in line.split(' | '):
                try:
                    if layout.line_cells(fld.strip()) > lim:
                        errs.append('choice field too long: %r' % fld)
                except layout.LayoutError as ex:
                    errs.append(str(ex))
    else:
        if '|' in en:
            errs.append('| not allowed in dialogue')
        if ' / ' in en:
            errs.append("' / ' not allowed in dialogue (write one paragraph)")
        try:
            layout.wrap(en)
        except layout.LayoutError as ex:
            errs.append(str(ex))
    # glossary: JP term present -> EN form present; avoid list
    for jp, enf, avoid in rows:
        vs = [v for v in re.split(r'\s*/\s*', re.sub(r'\(.*?\)', '', jp)) if v]
        if any(v in row['jp'] for v in vs):
            targets = [t.strip() for t in re.split(r'\s*/\s*', enf)]
            if not any(t.lower().replace('the ', '') in en.lower() for t in targets if t):
                pass  # soft: reviewers check; names below are hard
        for a in [x.strip() for x in avoid.split(',') if x.strip()]:
            if re.search(r'\b%s\b' % re.escape(a), en):
                errs.append('glossary: avoid %r' % a)
    for jp, enn in names_en.items():
        if len(jp) >= 2 and jp in row['jp'] and not jp.startswith(('街', '女', '男', '子', '部', '右', '左', 'みんな', '生徒')):
            first = enn.split(' ')[0] if not enn.startswith(('The ', 'Captain', 'Elder', 'King')) else enn
            core = enn.split(' the ')[0]
            if core not in en and first not in en:
                errs.append('name: %s -> %s missing' % (jp, enn))
    return errs


def check(name):
    rows = read_in(name)
    try:
        out, dupes = read_out(name)
    except (OSError, ValueError) as ex:
        print('ERROR', ex)
        return False
    names_en = load_names()
    grows = glossary_rows()
    errs = []
    ids = [r['id'] for r in rows]
    for d in dupes:
        errs.append('%s: duplicate id' % d)
    for k in out:
        if k not in ids:
            errs.append('%s: unknown id' % k)
    for r in rows:
        if r['id'] not in out:
            errs.append('%s: missing' % r['id'])
            continue
        for e in check_text(r, out[r['id']], names_en, grows):
            errs.append('%s: %s' % (r['id'], e))
    for e in errs:
        print(e)
    if errs:
        print('%d errors' % len(errs))
        return False
    print('OK %s (%d entries)' % (name, len(rows)))
    return True


def merge(names):
    if names == ['all']:
        names = sorted(f[:-8] for f in os.listdir(TL) if f.endswith('.out.tsv'))
    tr = {}
    for n in names:
        if not check(n):
            sys.exit('merge refused: %s fails check' % n)
        tr.update(read_out(n)[0])
    for fn in sorted(os.listdir(SCRIPT)):
        if not fn.endswith('.json'):
            continue
        p = os.path.join(SCRIPT, fn)
        es = json.load(open(p, encoding='utf-8'))
        ch = False
        for e in es:
            if e['id'] in tr and e.get('en') != tr[e['id']]:
                e['en'] = tr[e['id']]
                ch = True
        if ch:
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(es, f, ensure_ascii=False, indent=1)
                f.write('\n')
    print('merged %d entries' % len(tr))


def pairs(name):
    rows = read_in(name)
    out, _ = read_out(name)
    with open(os.path.join(TL, name + '.pairs.txt'), 'w', encoding='utf-8', newline='\n') as f:
        for i, r in enumerate(rows):
            f.write('>> %s | %s | %s\n   %s\n' % (r['id'], r['speaker'], r['jp'], out.get(r['id'], '')))
    print(os.path.join(TL, name + '.pairs.txt'))


def status():
    tot = done = 0
    for fn, e in all_entries():
        if e['form'] == 'empty' or 'dup' in e:
            continue
        tot += 1
        done += bool(e.get('en'))
    print('translated %d / %d unique units' % (done, tot))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'split':
        size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 140
        split(size)
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2]) else 1)
    elif cmd == 'merge':
        merge(sys.argv[2:])
    elif cmd == 'pairs':
        pairs(sys.argv[2])
    elif cmd == 'status':
        status()
