# Dragon Knight 4 English translation

Unofficial English fan translation of **Dragon Knight 4** (SNES, Banpresto, 1996): the source text and tools
that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `ui/` | Menu, status and battle-panel text; enemy names. |
| `glossary.md` | Binding names, terms and style rules. |
| `build.py`, `tools/` | Python build chain: extract, insert, lint, release. |
| `asm/` | Engine hooks (far text calls, variable-width font), assembled with asar. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |

## Build your own patched ROM

Needs Python 3.12+, [asar](https://github.com/RPGHacker/asar) 1.91 in `tools/asar/`, and your own dump of the
Japanese game.

```sh
git clone https://github.com/minhnhattonthat/dragon-knight-4
cd dragon-knight-4
# copy your dump to: rom/Dragon Knight 4 (Japan).sfc
#   (3145728 bytes, SHA-1 cfb5d2ce3eab576dae49f570284b75c1a8c0465d; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py                                # -> build/dk4_en.sfc
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is elf / Banpresto's and is included only
so the translation can be checked against it. Dragon Knight 4 is (c) 1996 elf / Banpresto; this project is not
affiliated with them. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
