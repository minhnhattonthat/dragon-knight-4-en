"""Extract the script into script/bNN_<blockoff>.json (one file per unique script block).

python -X utf8 tools/extract.py            # writes only missing files
python -X utf8 tools/extract.py --merge    # rewrite every file, keeping existing 'en' by id (never clobbers English)
Entry: {id, speaker, form, nlines, jp, en, dup?}. id = <blockoff>_<regionoff>.<segment>. 'dup' = id of the first
identical unit (same form, speaker, jp); the builder uses that unit's English when 'en' is empty.
"""
import json
import os
import sys
from dk4 import ROOT, load_rom, load_glyphs
from regions import regions
from segments import units


def build_entries():
    rom, g = load_rom(), load_glyphs()
    files, first = {}, {}
    for r in regions(rom, g):
        fn = 'b%02d_%06X.json' % (r['block'], r['boff'])
        for u in units(r, rom, g):
            e = {'id': '%s.%d' % (r['id'], u['sid']), 'speaker': u['speaker'], 'form': u['form'],
                 'nlines': u['nlines'], 'jp': u['jp'], 'en': ''}
            key = (u['form'], u['speaker'], u['jp'])
            if u['form'] != 'empty':
                if key in first:
                    e['dup'] = first[key]
                else:
                    first[key] = e['id']
            files.setdefault(fn, []).append(e)
    return files


def main():
    merge = '--merge' in sys.argv
    out = os.path.join(ROOT, 'script')
    os.makedirs(out, exist_ok=True)
    files = build_entries()
    wrote = 0
    for fn, entries in files.items():
        p = os.path.join(out, fn)
        if os.path.exists(p):
            if not merge:
                continue
            old = {e['id']: e for e in json.load(open(p, encoding='utf-8'))}
            for e in entries:
                if e['id'] in old:
                    for k in ('en', 'notes'):
                        if old[e['id']].get(k):
                            e[k] = old[e['id']][k]
            lost = [i for i, e in old.items() if e.get('en') and i not in {x['id'] for x in entries}]
            if lost:
                sys.exit('refusing: %s would lose English for %s' % (fn, lost[:5]))
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)
            f.write('\n')
        wrote += 1
    n = sum(len(v) for v in files.values())
    u = sum(1 for v in files.values() for e in v if 'dup' not in e and e['form'] != 'empty')
    print('files %d (wrote %d), units %d, unique %d' % (len(files), wrote, n, u))


if __name__ == '__main__':
    main()
