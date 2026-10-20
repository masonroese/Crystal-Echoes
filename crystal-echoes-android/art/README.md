# Character sprite sheets

Each character can have one sprite sheet. Until it has one, the game draws its current figure.

## The sheet

- One PNG per character, 432 × 192 pixels, transparent background.
- 9 columns × 4 rows of 48 × 48 cells. `sprite-template-guide.png` shows every cell, labelled.
  `sprite-template.png` is the same grid at actual size with faint guides, to use as a hidden layer.
- Art faces **right**. The game mirrors it for left (walk left, walk up-left, walk down-left, attack left).
- The centre of each cell is where the character stands in the arena. The orange circle is the body
  hitbox (22 px across). Weapons, capes and effects can go outside the circle but must stay inside the cell.
- All upgrade tiers use the same sheet; upgraded characters get a crystal-coloured glow in the game.

| Row | Cells |
|---|---|
| 1 | idle · damaged · death |
| 2 | walk right 1–3 · walk up 1–3 · walk down 1–3 |
| 3 | walk up-right 1–3 · walk down-right 1–3 |
| 4 | attack right 1–3 · attack up 1–3 · attack down 1–3 |

## When each frame shows

- **Idle**: standing still, and on the character select screen.
- **Walk**: while moving, in the direction of movement, cycling through the 3 frames.
- **Attack**: when the ability is used, towards the aim or facing; diagonal attacks use the right/left frames.
  The Ranger shows attack 1 while drawing its bow and attack 2 at full draw.
- **Damaged**: while frozen, or briefly when Ben's shield blocks a hit on the character.
- **Death**: after being knocked out (a moment of the damaged frame first).

Empty cells are fine: the game falls back (diagonal walk → walk right, attack up/down → attack right,
anything else → idle), so a sheet can be added before it is finished.

## Adding a sheet

1. Save it as `www/sprites/<character>.png` using one of these names:
   `ninja`, `ranger`, `ghost`, `sprinter`, `trapper`, `frost`, `ben`, `time`, `sniper`.
2. Add the name to `SHEETS` near the top of the character-sprite section of `www/index.html`,
   for example `const SHEETS=['ninja'];`.
