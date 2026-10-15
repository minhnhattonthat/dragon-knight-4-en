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
- 様 from townsfolk/soldiers to the legendary heroes (Takeru, Bahn) -> "Lord Takeru"/"Lord Bahn" is accepted.
  おにーさん (Eto insisting he is not old) -> "young man" (vs "mister"/"old man" for おじさん).
- Squad names: 剣士隊 = Swordsman Squad, 弓術隊 = Archery Squad, 砲術隊 = Gunnery Squad, 騎馬隊 = Cavalry Squad,
  魔導師隊 = Sorcerer Squad; a person's squad: ゴロンゴン隊 = "Gorongon's Squad" (choice menus too).
- The Japanese text was read from the font by eye; a few kanji may be look-alikes (惜 for 憎, 曉 for 眺,
  遠庫 for 遠慮). If a word makes no sense, read the look-alike that fits.
- Rabbit's にょ -> ", nyo" at sentence end ("I'm fine, nyo..."). Powell's ござる -> stiff archaic speech
  ("good sir", "pray tell"). Charon's カケル殿 -> "Master Kakeru".
- Tanyan's にゃん -> ", nya". ぽっ -> "*blush*". 守備隊 -> garrison. やめる in a choice menu -> "Cancel".
- Seil is a boy (Bahn's son, Kakeru's friend). 工作隊 = Sapper Squad, 忍者隊 = Ninja Squad.
  Spell ハリタ・ハリティ・ブラスティ = "Harita Haritee Blastee". 乙乙乙 = snoring "Zzz...".
  If the checker wants a name you dropped, rephrase with the Write tool (never sed).
- 闇の世界 = the World of Darkness, 闇の扉 = the Door of Darkness. Speech tics: Galivan だぞい -> "I tell ye";
  Linus baby talk -> w-for-r lisp. Puzzle passwords in kana (ちぬたたぬち) are romanized letter for letter.
- Six dots "......" only for a silent beat on its own; trailing dots in speech are "...".
- 『』 -> single quotes.
- Deliberate name mix-ups in the Japanese (e.g. Kakeru calling Torhes "Hortes") stay mix-ups.
- 殿 from guards/servants to Kakeru -> "Master Kakeru". おじさん to a stranger -> "mister" (keep jokes about
  おじさん vs おにいさん as "mister" vs "big brother"/"old man" vs "young man").

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`.
