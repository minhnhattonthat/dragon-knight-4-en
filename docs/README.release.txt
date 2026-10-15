Dragon Knight 4 (SNES) - English translation patch v{version}
===========================================================

Unofficial fan translation. No ROMs are included or provided; patch your own dump.

Patch: {patch} (BPS). Apply with Floating IPS (Flips), beat, or RomPatcher.js.

Base ROM (No-Intro): Dragon Knight 4 (Japan).sfc
  Size   {size} bytes (3 MiB, unheadered)
  CRC32  {ocrc}
  MD5    {omd5}
  SHA-1  {osha}

Patched ROM ({psize} bytes, 4 MiB: the patch expands the ROM for the English text and font):
  CRC32  {bcrc}
  SHA-1  {bsha}

What is translated
- All story, town, battle and ending dialogue (12,103 unique lines, every script block plus the ending
  epilogue), with a new variable-width English font; long lines continue on extra pages automatically.
- Menus: main/field menu, options, notebooks (save/load), status screen, party list, item screen,
  battle panel, unit types, unit info box, the 206-entry name table, combat screen labels.
- Battle command buttons (Wait / Attack / Heal / Break) redrawn in English.
- The title logo, "Player Phase" banners and the staff roll were already in English in the original.

Names: no official English romanization exists; the hero is Kakeru, the villain Lushifon (as in English
references to the PC-98 games). Honorifics are dropped; given names come first.

Notes
- Start from a cold boot after patching (do not load savestates made with the Japanese ROM).
  Battery saves (notebooks) are compatible: the save format is untouched.
- Tested in MesenCE 2.2.1.

Known issues
- The battle panel shows "Gnd" (Ground) for the ground-unit percentage: the slot fits 3 letters.
- The surrender popup reads "Yield?" (the popup graphics have room for 128 tiles only).
- The unit information box uses a narrow font so its columns stay inside the window.
- A name the game inserts into a sentence keeps its fixed width, so a small gap can appear before
  the comma that follows it ("Rabbit , I want you to...").
- The battle animation screen could not be reached by the automated tests; no Japanese is expected
  there, but it was not seen.
- Please report anything odd with the screen and a screenshot.

Credits
- Translation, font, VWF engine and graphics: fan translation produced with AI assistance (Claude,
  Anthropic) and automated emulator QA. Original game (c) 1996 elf / Banpresto.
- No earlier English patch for the SNES version was found (fan patches exist for the PC-98/DOS
  versions; none of their text was used).
