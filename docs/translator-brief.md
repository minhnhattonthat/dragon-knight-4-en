# Translator brief - Dragon Knight 4 (SNES, Banpresto/elf, 1996)

You translate part of the Japanese script of Dragon Knight 4 into English for a fan patch. It is a fantasy strategy
RPG with lots of comedy: Kakeru (a cheeky, girl-crazy 15-year-old, son of the legendary hero Takeru and the
sorceress Luna) and Eto (a proud, gruff masked swordsman) fight the demon Lushifon's army with a growing band of
allies. The SNES version is all-ages; keep innuendo as innuendo.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.
Repo root: H:\translation\batch\projects\dragon-knight-4 (run commands from there).

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (full table in `glossary.md`; every speaker
   tag spelling is in `tbl/names_en.tsv` - use the same spellings when a name appears inside dialogue).

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`
- speaker: the English name tag the game shows (already translated; do NOT write it in your English). `-` = no
  tag: the line continues the previous speaker's speech, or is narration.
- form `dlg`: one speech. ` / ` in the Japanese marks where the original box broke lines - translate the whole
  thing as ONE paragraph; the build wraps it and adds pages as needed (no length cuts needed, but keep it natural:
  limit is only a soft guide).
- form `choice`: menu options. ` / ` separates option lines and ` | ` separates columns on one line. Keep exactly
  the same number of lines and columns, each option short (max ~20 characters per column).
- Lines are in story order: use neighbours for context. Consecutive entries with the same region id
  (the part before the dot) are one continuous conversation.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`. Never use `{` `}` `|` (and ` / ` only in choices).

## Validate
Run `python -X utf8 tools/batches.py check <batch>` and fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt jokes and wordplay so they still land (no translator notes).
- Names and terms exactly as in the glossary. Never abbreviate. Honorifics are dropped (様 on a lord/master ->
  "Lord X"/"Lady X"; さん/ちゃん/君 -> nothing, convey closeness through tone). Given name first.
- Punctuation: 「」 -> "...", …… -> "...", ！！ -> "!!", ！？ -> "?!", （ ） -> ( ) for thoughts/asides.
- Stutters: "W-wait!". Sound effects and laughs in English ("Wahaha!", "Ku ku ku...", "Munch munch").
- `……。` alone -> "......"; `！？` alone -> "!?".
- Numbers in text are literal (no variables); write "7 Seeds of Power" style naturally.
- Kakeru: casual, cheeky boy ("Dad", "Yay!", "c'mon"). Eto: commanding, curt, a bit pompous ("Hmph."). Lushifon
  and Minax: formal, archaic villain register. Children talk like children.

## Notes from earlier batches
- レイモンド王国 = "the Kingdom of Raymond"; レイモンド王 = "the King of Raymond". The checker now tells them apart.
- Name checks are case-insensitive and allow drawn-out shouts ("SEEEIL!!", "Torhes!!").
- 〜隊 after a name = "Cartas's Squad" style ("the X Squad"), never "Unit". ヴェルトー = Verto (Hardis's dragon).
  魔導師 = sorcerer, 魔導師学校 = the School of Sorcery. Japanese typos (運ばう = 運ぼう) are read as intended.
- Deliberate name mix-ups in the Japanese (e.g. Kakeru calling Torhes "Hortes") stay mix-ups.
- 殿 from guards/servants to Kakeru -> "Master Kakeru". おじさん to a stranger -> "mister" (keep jokes about
  おじさん vs おにいさん as "mister" vs "big brother"/"old man" vs "young man").

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`.
