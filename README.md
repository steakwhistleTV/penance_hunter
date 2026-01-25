# Penance Hunter

Track and visualize your Warhammer 40,000: Darktide penance progress.

**[Launch Web App](https://steakwhistletv.github.io/penance_hunter/)** | **[Beta Version](https://steakwhistletv.github.io/penance_hunter/beta/penance_hunter.html)**

## Quick Start

### 1. Export Your Penances (In-Game)

1. Install the mod (requires [Darktide Mod Framework](https://www.nexusmods.com/warhammer40kdarktide/mods/8))
2. Copy `penance_exporter/` to `%APPDATA%/Fatshark/Darktide/mods/`
3. Add `penance_exporter` to `mod_load_order.txt`
4. In-game: Open Penances menu, press **F9** (or `/export_penances`)
5. CSV saved to `%APPDATA%/Fatshark/Darktide/penance_exporter/`

### 2. View Your Data

**Web (recommended):** Go to [steakwhistletv.github.io/penance_hunter](https://steakwhistletv.github.io/penance_hunter/), drop your CSV. All processing is local.

**Local:** `uvx marimo run apps/penance_hunter.py`

## Features

- Account overview with completion %, levels, prestige
- All operatives with individual stats
- Category & class breakdown charts
- Progress timeline with date filtering
- Filterable penance list
- Track specific penances
- **Beta:** Save/load tracking profiles

## CSV Format

The mod exports CSV with comment header containing account metadata, followed by penance data.

<details>
<summary>Header fields (comments)</summary>

| Field | Description |
|-------|-------------|
| Mod Version | Version of penance_exporter |
| Account | Display name |
| Account Level | Sum of character base levels |
| Account True Level | Sum including prestige |
| Account Prestige | Sum of all prestiges |
| All Characters | List with name, class, level, true level, prestige |
| Export Timezone | Local timezone offset |

</details>

<details>
<summary>Penance data fields</summary>

| Field | Description |
|-------|-------------|
| Achievement_ID | Unique identifier |
| Category | Category localization key |
| Title | Display name |
| Description | Requirements text |
| Status | Completed / In Progress |
| Progress / Goal | Current and target values |
| Completion_Time | When completed |
| Score | Points awarded |

</details>

<details>
<summary>How the mod works</summary>

The mod hooks into `PenanceOverviewView` to access achievement data:

1. Retrieves achievement list from `view._achievements_by_category`
2. Gets definitions via `AchievementUIHelper.achievement_definition_by_id()`
3. Checks completion with `Managers.achievements:achievement_completed()`
4. Reads progress from `AchievementTypes[definition.type].get_progress()`

Requires penance menu to be open (that's when Darktide loads the data).

</details>

## Development

```bash
git clone https://github.com/steakwhistleTV/penance_hunter.git
cd penance_hunter
uvx marimo edit apps/penance_hunter_beta.py  # Edit beta
uvx marimo run apps/penance_hunter.py        # Run stable
```

```
apps/
  penance_hunter.py        # Stable
  penance_hunter_beta.py   # Beta
  public/                  # Sample data
penance_exporter/
  scripts/mods/penance_exporter/
    penance_exporter.lua   # Main mod
```

## References

- [Darktide Mod Framework](https://dmf-docs.darkti.de/)
- [Darktide Source Code](https://github.com/Aussiemon/Darktide-Source-Code) - Achievement system in `scripts/managers/achievements/`
- [marimo](https://marimo.io)
