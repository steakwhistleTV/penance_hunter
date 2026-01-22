# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "marimo",
#     "pandas==2.3.3",
#     "pyfiglet==1.0.4",
#     "pyarrow",
# ]
# [tool.marimo.display]
# theme = "dark"
# ///

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import io
    import sys
    import re
    import pyfiglet
    return alt, io, mo, pd, pyfiglet, re, sys


@app.cell(hide_code=True)
def _(mo, pyfiglet):
    nurgle_ascii = pyfiglet.figlet_format("Penance Hunter", font="bloody", width=200)
    penance_title = pyfiglet.figlet_format("notebook visualizer 40k", font="double_blocky", width=200)

    _output = mo.Html(f"<pre style='text-align: center; font-family: monospace; color: #8b0000; text-shadow: 0 0 10px #5c0000, 0 2px 4px #000;'>{nurgle_ascii}\n{penance_title}</pre>")
    _output.center()
    return


@app.cell
def _(csv_upload):
    csv_upload
    return


@app.cell(hide_code=True)
def _(mo):
    _sidebar_title = mo.Html("""
        <link href="https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap" rel="stylesheet">
        <h1 style="font-family: 'UnifrakturCook', cursive; font-size: 1.8rem;  text-shadow: 0 0 8px #5c0000;">
            Penance Hunter
        </h1>
    """)

    mo.sidebar(
        [
            _sidebar_title,
            mo.nav_menu(
                {
                    "https://github.com/steakwhistleTV/penance_hunter": f"::lucide:github:: Project README",
                    "https://github.com/steakwhistleTV/penance_hunter/tree/main/penance_exporter": f"::lucide:package:: Penance Exporter Mod",
                },
                orientation="vertical",
            ),
        ],
        footer=mo.md("_Don't ever say N**gle..._"),
    )
    return


@app.cell(hide_code=True)
def _(mo, sys):
    default_csv = mo.notebook_location() / "public" / "00000000-0000-0000-0000-000000000000_20260118_103938.csv"

    def is_wasm() -> bool:
        return "pyodide" in sys.modules

    csv_upload = mo.ui.file(
        filetypes=[".csv"],
        multiple=False,
        kind="area",
        label="Drop your penance export CSV here, or click to browse",
    )
    return csv_upload, default_csv, is_wasm


@app.cell
def _(csv_upload, default_csv, io, is_wasm, mo, pd, re):
    # Load CSV data
    if csv_upload.value:
        penance_export_filename = csv_upload.name()
        penance_export_contents = csv_upload.contents()
    else:
        penance_export_filename = default_csv.name
        if is_wasm():
            import pyodide.http
            resp = pyodide.http.open_url(str(default_csv))
            penance_export_contents = resp.read().encode("utf-8")
        else:
            penance_export_contents = default_csv.read_bytes()

    # Parse CSV
    print(f"~ now reading file: {penance_export_filename} ({type(penance_export_contents)})")
    penances_df = pd.read_csv(io.BytesIO(penance_export_contents), comment='#')
    print(f"~ created dataframe from penance export ({len(penances_df)} rows)")

    # label with source export file
    penances_df['EXPORT_FILE'] = penance_export_filename
    penances_df['EXPORT_FILE'] = penances_df['EXPORT_FILE'].astype(str)

    penances_df['Completion_Time'] = pd.to_datetime(penances_df['Completion_Time'], errors='coerce')

    # regex for extracting timestamps and dates from export filenames
    match = re.search(r'[0-9a-f-]+_([0-9]{8})_[0-9]{6}\.csv', str(penance_export_filename))
    ts_match = re.search(r'[0-9a-f-]+_([0-9]{8})_([0-9]{6})\.csv', str(penance_export_filename))

    # extract export date from filename
    penances_df['EXPORT_DATE'] = match.group(1).title() if match else "Unknown"

    if ts_match:
        ts_string = ts_match.group(1) + ts_match.group(2)
        export_timestamp = pd.to_datetime(ts_string, format='%Y%m%d%H%M%S', errors='coerce')
    else:
        export_timestamp = pd.NaT

    # Extract account metadata from CSV comments
    def get_account_metadata(contents):
        meta = {'all_characters': []}
        in_characters_section = False
        with io.TextIOWrapper(io.BytesIO(contents), encoding="utf-8") as f:
            for line in f:
                if not line.startswith('#'):
                    break
                line_stripped = line.lstrip('#').strip()
                if 'All Characters:' in line_stripped:
                    in_characters_section = True
                    continue
                if in_characters_section:
                    if line_stripped and line_stripped[0].isdigit():
                        meta['all_characters'].append(line_stripped)
                    elif not line_stripped or 'Export Character:' in line_stripped:
                        in_characters_section = False
                if 'Account ID:' in line_stripped:
                    meta['account_id'] = line_stripped.split(':', 1)[1].strip()
                elif 'Account Level:' in line_stripped:
                    meta['account_level'] = int(line_stripped.split(':')[1].strip())
                elif 'Account True Level:' in line_stripped:
                    meta['account_true_level'] = int(line_stripped.split(':')[1].strip())
                elif 'Account Prestige:' in line_stripped:
                    meta['prestige'] = int(line_stripped.split(':')[1].strip())
                elif 'Export Timezone:' in line_stripped:
                    meta['timezone'] = line_stripped.split(':', 1)[1].strip()
                elif 'Mod Version:' in line_stripped:
                    meta['mod_version'] = line_stripped.split(':', 1)[1].strip()
        return meta

    account_meta = get_account_metadata(penance_export_contents)

    # Calculate derived columns
    penances_df['PROGRESS_DIFF'] = penances_df['Goal'] - penances_df['Progress']
    penances_df = penances_df.sort_values('Completion_Time')
    penances_df['CUMULATIVE_COUNT'] = range(1, len(penances_df) + 1)

    # Create sub-dataframes
    completed_df = penances_df[penances_df['Status'] == 'Completed'].copy()
    completed_df['Completion_Date'] = completed_df['Completion_Time'].dt.date

    active_df = penances_df[penances_df['Status'] == 'In Progress'].copy()
    active_df = active_df.sort_values(by='Progress_Percentage', ascending=False)

    mo.stop(False)  # Always continue
    return account_meta, completed_df, export_timestamp, penances_df


@app.cell
def _(account_meta, completed_df, export_timestamp, mo, penances_df):
    # Account info header
    account_name = penances_df['Export_Account'].iloc[0] if 'Export_Account' in penances_df.columns else "Unknown"
    character_name = penances_df['Export_Character'].iloc[0] if 'Export_Character' in penances_df.columns else "Unknown"

    total_penances = len(penances_df)
    total_completed = len(completed_df)
    completion_pct = round(total_completed / total_penances * 100, 1)

    # Get completion time stats
    earliest_completion = completed_df['Completion_Time'].min()
    latest_completion = completed_df['Completion_Time'].max()

    # Get timezone from export metadata
    timezone_str = account_meta.get('timezone', '')

    # Format timestamps with time and seconds
    export_time_str = export_timestamp.strftime('%Y-%m-%d %H:%M:%S') if not export_timestamp != export_timestamp else "Unknown"
    earliest_str = earliest_completion.strftime('%Y-%m-%d %H:%M:%S') if not earliest_completion != earliest_completion else "N/A"
    latest_str = latest_completion.strftime('%Y-%m-%d %H:%M:%S') if not latest_completion != latest_completion else "N/A"

    # Main stats row
    _stats = [
        mo.stat(label="Completed", value=f"{total_completed}/{total_penances}", bordered=True),
        mo.stat(label="Completion %", value=f"{completion_pct}%", bordered=True),
        mo.stat(label="Account Level", value=account_meta.get('account_level', 'N/A'), bordered=True),
        mo.stat(label="True Level", value=account_meta.get('account_true_level', 'N/A'), bordered=True),
        mo.stat(label="Prestige", value=account_meta.get('prestige', 'N/A'), bordered=True),
    ]

    # Time stats row
    _time_stats = [
        mo.stat(label="Export Time", value=export_time_str, bordered=True),
        mo.stat(label="First Completion", value=earliest_str, bordered=True),
        mo.stat(label="Latest Completion", value=latest_str, bordered=True),
        mo.stat(label="Timezone", value=timezone_str if timezone_str else "N/A", bordered=True),
    ]

    # Operatives list
    all_chars = account_meta.get('all_characters', [])

    if all_chars:
        import re as _re
        _class_mapping = {
            'veteran': 'Veteran',
            'zealot': 'Zealot',
            'zelot': 'Zealot',
            'psyker': 'Psyker',
            'ogryn': 'Ogryn',
            'adamant': 'Arbitrator',
            'broker': 'Hive Scum'
        }
        _char_stats = []
        for char in all_chars:
            # Parse: "1. gern (Zealot) - Level 30 (True: 169, Prestige: 4)" or "2. Zek (Hive Scum) - Level 30"
            char_match = _re.match(r'\d+\.\s*(.+?)\s*\(([^)]+)\)\s*-\s*Level\s*(\d+)(?:\s*\(True:\s*(\d+),\s*Prestige:\s*(\d+)\))?', char)
            if char_match:
                name, cls, level, true_level, prestige = char_match.groups()
                # Map class names (adamant -> Arbitrator, broker -> Hive Scum)
                display_cls = _class_mapping.get(cls.lower(), cls.title())
                if true_level and prestige:
                    caption = f"Level {level} (True: {true_level}, Prestige: {prestige})"
                else:
                    caption = f"Level {level}"
                _char_stats.append(mo.stat(label=display_cls, caption=caption, value=name, bordered=True))
            else:
                _char_stats.append(mo.stat(label="Unknown", value=char, bordered=True))
        _operatives_section = mo.vstack([
            mo.md("#### ::lucide:users:: Operatives"),
            mo.hstack(_char_stats, widths="equal", align="center")
        ])
    else:
        _operatives_section = None

    mod_version = account_meta.get('mod_version', 'Legacy')
    version_str = f" (v{mod_version})"
    _header = mo.md(f"### **{account_name}** - exported by {character_name}{version_str}")

    _content = [
        _header,
        mo.hstack(_stats, widths="equal", align="center"),
        mo.hstack(_time_stats, widths="equal", align="center"),
    ]
    if _operatives_section:
        _content.append(_operatives_section)

    mo.vstack(_content)
    return


@app.cell
def _(is_wasm, mo, penances_df):
    # Create dataframes per in-game mapped category
    _class_mapping = {
        'veteran': 'Veteran',
        'zealot': 'Zealot',
        'zelot': 'Zealot',
        'psyker': 'Psyker',
        'ogryn': 'Ogryn',
        'adamant': 'Arbitrator',
        'broker': 'Hive Scum'
    }

    def _extract_class(achievement_id):
        achievement_id_lower = achievement_id.lower()
        for class_key, class_value in _class_mapping.items():
            if class_key in achievement_id_lower:
                return class_value
        return 'Unknown'

    # 1. Account Penances
    account_df = penances_df[penances_df['Category'].isin(['loc_achievement_category_account_label'])]
    account_completed = len(account_df[account_df['Status'] == 'Completed'])
    account_total = len(account_df)

    # 2. Class Penances
    class_df = penances_df[penances_df['Category'].isin(['loc_class_abilities_title', 'loc_class_progression_title'])].copy()
    class_df['Penance_Class'] = class_df['Achievement_ID'].apply(_extract_class)
    class_summary = class_df.groupby('Penance_Class')['Status'].agg(
        total='size',
        completed=lambda s: (s == 'Completed').sum()
    ).astype({'total': int, 'completed': int})
    class_summary['pct'] = (class_summary['completed'] / class_summary['total'] * 100).round(0).astype(int)

    # 3. Tactical Penances
    tactical_df = penances_df[penances_df['Category'].isin([
        'loc_achievement_category_offensive_label',
        'loc_achievement_category_defensive_label',
        'loc_achievement_category_teamplay_label'
    ])]
    tactical_completed = len(tactical_df[tactical_df['Status'] == 'Completed'])
    tactical_in_progress = len(tactical_df[tactical_df['Status'] == 'In Progress'])

    # 4. Heretical Penances
    heretical_df = penances_df[penances_df['Category'].isin(['loc_achievement_category_heretics_label'])]
    heretical_completed = len(heretical_df[heretical_df['Status'] == 'Completed'])

    # 5. Missions Penances
    missions_df = penances_df[penances_df['Category'].isin([
        'loc_achievement_subcategory_missions_general_label',
        'loc_achievement_subcategory_missions_auric_label',
        'loc_achievement_subcategory_missions_havoc_label',
        'loc_achievement_subcategory_missions_survival_label'
    ])]
    missions_completed = len(missions_df[missions_df['Status'] == 'Completed'])
    missions_in_progress = len(missions_df[missions_df['Status'] == 'In Progress'])

    # 6. Exploration Penances
    exploration_terms = ['group_mission_zone_wide', 'collectible', 'destructible', 'mission_zone_',
                         'mission_scavenge_samples', 'mission_propaganda_fan_kills', 'mission_raid_bottles']
    exploration_regex = '|'.join(exploration_terms)
    exploration_df = penances_df[
        (penances_df['Achievement_ID'].str.contains(exploration_regex, case=False, na=False)) |
        (penances_df['Category'].isin(['loc_achievement_subcategory_twins_mission_label']))
    ]
    exploration_completed = len(exploration_df[exploration_df['Status'] == 'Completed'])

    # 7. Endeavours Penances (leftover)
    excluded_categories = [
        'loc_class_abilities_title', 'loc_class_progression_title',
        'loc_achievement_category_account_label',
        'loc_achievement_category_offensive_label', 'loc_achievement_category_defensive_label',
        'loc_achievement_category_teamplay_label', 'loc_achievement_category_heretics_label',
        'loc_achievement_subcategory_missions_general_label', 'loc_achievement_subcategory_missions_auric_label',
        'loc_achievement_subcategory_missions_havoc_label', 'loc_achievement_subcategory_missions_survival_label',
        'loc_achievement_subcategory_twins_mission_label',
        'loc_weapon_progression_mastery', 'loc_achievement_category_weapons_label'
    ]
    leftover_df = penances_df[~penances_df['Category'].isin(excluded_categories)]
    leftover_df = leftover_df[~leftover_df['Achievement_ID'].str.contains(exploration_regex, case=False, na=False)]
    endeavours_completed = len(leftover_df[leftover_df['Status'] == 'Completed'])

    # 8. Weapons Penances
    weapons_df = penances_df[penances_df['Category'].isin([
        'loc_weapon_progression_mastery', 'loc_achievement_category_weapons_label'
    ])]
    weapons_completed = len(weapons_df[weapons_df['Status'] == 'Completed'])

    # All categories in one row
    _cat_stats = [
        mo.stat(label="Account", value=f"{account_completed}", caption="Completed", bordered=True),
        mo.stat(label="Tactical", value=f"{tactical_completed}", caption=f"{tactical_in_progress} in progress" if tactical_in_progress else "Completed", bordered=True),
        mo.stat(label="Heretical", value=f"{heretical_completed}", caption="Completed", bordered=True),
        mo.stat(label="Missions", value=f"{missions_completed}", caption=f"{missions_in_progress} in progress" if missions_in_progress else "Completed", bordered=True),
        mo.stat(label="Exploration", value=f"{exploration_completed}", caption="Completed", bordered=True),
        mo.stat(label="Endeavours", value=f"{endeavours_completed}", caption="Completed", bordered=True),
        mo.stat(label="Weapons", value=f"{weapons_completed}", caption="Completed", bordered=True),
    ]

    # Class penances per class with icons (base64 encoded for browser compatibility)
    import base64
    _icons_path = mo.notebook_location() / "public" / "icons"

    def _load_icon(icon_name):
        icon_path = _icons_path / f'{icon_name}.png'
        try:
            if is_wasm():
                # In WASM, use the path directly as URL - browser fetches it
                return str(icon_path)
            else:
                # Locally, base64 encode for embedded display
                with open(icon_path, 'rb') as f:
                    return f'data:image/png;base64,{base64.b64encode(f.read()).decode()}'
        except Exception as e:
            print(f"Failed to load icon {icon_name}: {e}")
            return ''

    _class_icons = {
        'Veteran': _load_icon('veteran'),
        'Zealot': _load_icon('zealot'),
        'Psyker': _load_icon('psyker'),
        'Ogryn': _load_icon('ogryn'),
        'Arbitrator': _load_icon('arbitrator'),
        'Hive Scum': _load_icon('hive_scum'),
    }

    _class_stats = []
    for _cls in ['Arbitrator', 'Hive Scum', 'Ogryn', 'Psyker', 'Veteran', 'Zealot']:
        if _cls in class_summary.index:
            _row = class_summary.loc[_cls]
            _icon_data = _class_icons.get(_cls, '')
            _card_html = f'''
            <div style="
                position: relative;
                border: 1px solid var(--border-color, #333);
                border-radius: 8px;
                padding: 12px 16px;
                text-align: center;
                background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(20,20,20,0.9) 100%);
                overflow: hidden;
            ">
                <img src="{_icon_data}" style="
                    position: absolute;
                    right: 8px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 48px;
                    height: 48px;
                    opacity: 0.3;
                ">
                <div style="position: relative; z-index: 1;">
                    <div style="font-size: 0.75rem; color: var(--text-muted, #888); margin-bottom: 4px;">{_cls}</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{int(_row['completed'])}/{int(_row['total'])}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted, #888);">{int(_row['pct'])}%</div>
                </div>
            </div>
            '''
            _class_stats.append(mo.Html(_card_html))

    mo.vstack([
        mo.md("#### ::lucide:trophy:: Categories"),
        mo.hstack(_cat_stats, widths="equal", align="center"),
        mo.md("##### ::lucide:swords:: Class Penances"),
        mo.hstack(_class_stats, widths="equal", align="center"),
    ])
    return


@app.cell(hide_code=True)
def _(completed_df, mo, pd):
    # Class mapping for extracting class from Achievement_ID
    _class_mapping = {
        'veteran': 'Veteran',
        'zealot': 'Zealot',
        'zelot': 'Zealot',
        'psyker': 'Psyker',
        'ogryn': 'Ogryn',
        'adamant': 'Arbitrator',
        'broker': 'Hive Scum'
    }

    def _extract_class(achievement_id):
        achievement_id_lower = achievement_id.lower()
        for class_key, class_value in _class_mapping.items():
            if class_key in achievement_id_lower:
                return class_value
        return 'General'

    # Prepare chart data with class info
    chart_base_df = completed_df.copy()
    chart_base_df['Penance_Class'] = chart_base_df['Achievement_ID'].apply(_extract_class)

    # Get date range from data
    min_date = chart_base_df['Completion_Time'].min()
    max_date = chart_base_df['Completion_Time'].max()

    # Class filter - multiselect
    available_classes = ['General', 'Arbitrator', 'Hive Scum', 'Ogryn', 'Psyker', 'Veteran', 'Zealot']
    chart_class_filter = mo.ui.multiselect(
        options=available_classes,
        value=available_classes,
        label="Classes"
    )

    # Date range filters
    chart_start_date = mo.ui.date(
        value=min_date.date() if pd.notna(min_date) else None,
        label="Start Date"
    )

    chart_end_date = mo.ui.date(
        value=max_date.date() if pd.notna(max_date) else None,
        label="End Date"
    )

    chart_use_now = mo.ui.checkbox(label="End at Now", value=False)

    mo.vstack([
        mo.md("#### ::lucide:chart-line:: Penance Progress Chart"),
        mo.hstack([
            chart_class_filter,
            chart_start_date,
            chart_end_date,
            chart_use_now
        ], justify="start", gap=1)
    ])
    return (
        chart_base_df,
        chart_class_filter,
        chart_end_date,
        chart_start_date,
        chart_use_now,
    )


@app.cell(hide_code=True)
def _(
    alt,
    chart_base_df,
    chart_class_filter,
    chart_end_date,
    chart_start_date,
    chart_use_now,
    mo,
    pd,
):
    # Apply filters
    filtered_chart_df = chart_base_df.copy()

    # Filter by selected classes
    if chart_class_filter.value:
        filtered_chart_df = filtered_chart_df[filtered_chart_df['Penance_Class'].isin(chart_class_filter.value)]

    # Filter by date range
    if chart_start_date.value:
        start_dt = pd.Timestamp(chart_start_date.value)
        filtered_chart_df = filtered_chart_df[filtered_chart_df['Completion_Time'] >= start_dt]

    if chart_use_now.value:
        end_dt = pd.Timestamp.now()
    elif chart_end_date.value:
        end_dt = pd.Timestamp(chart_end_date.value) + pd.Timedelta(days=1)  # Include full end day
    else:
        end_dt = None

    if end_dt:
        filtered_chart_df = filtered_chart_df[filtered_chart_df['Completion_Time'] <= end_dt]

    # Sort by completion time and calculate cumulative count per class
    filtered_chart_df = filtered_chart_df.sort_values('Completion_Time')
    filtered_chart_df['CCOUNT_PER_CLASS'] = filtered_chart_df.groupby('Penance_Class').cumcount() + 1

    # Get last point for each class (for endpoint markers)
    last_points = filtered_chart_df.groupby('Penance_Class').last().reset_index()

    # Determine x-axis domain
    if len(filtered_chart_df) > 0:
        x_min = filtered_chart_df['Completion_Time'].min()
        x_max = pd.Timestamp.now() + pd.Timedelta(days=5) if chart_use_now.value else (end_dt + pd.Timedelta(days=5) if end_dt else pd.Timestamp.now() + pd.Timedelta(days=5))

        # Line chart for progression
        line_chart = alt.Chart(filtered_chart_df).mark_line(point=True).encode(
            x=alt.X('Completion_Time:T', title='Date', scale=alt.Scale(domain=[x_min, x_max])),
            y=alt.Y('CCOUNT_PER_CLASS:Q', title='Penances Completed'),
            color=alt.Color('Penance_Class:N', title='Class'),
            tooltip=[
                alt.Tooltip('Penance_Class:N', title='Class'),
                alt.Tooltip('Completion_Time:T', title='Date'),
                alt.Tooltip('CCOUNT_PER_CLASS:Q', title='Total for Class'),
                alt.Tooltip('Title:N', title='Penance')
            ]
        )

        # Endpoint markers
        last_points_chart = alt.Chart(last_points).mark_point(size=200, filled=True).encode(
            x=alt.X('Completion_Time:T', scale=alt.Scale(domain=[x_min, x_max])),
            y=alt.Y('CCOUNT_PER_CLASS:Q'),
            color=alt.Color('Penance_Class:N', title='Class'),
            tooltip=[
                alt.Tooltip('Penance_Class:N', title='Class'),
                alt.Tooltip('Completion_Time:T', title='Date'),
                alt.Tooltip('CCOUNT_PER_CLASS:Q', title='Total for Class')
            ]
        )

        # Layer together
        class_progression_chart = (
            line_chart + last_points_chart
        ).properties(
            width="container",
            height=400,
            title="Operative Penance Progress by Class"
        ).interactive()

        _chart_output = mo.ui.altair_chart(class_progression_chart, chart_selection=False)

        # Stats for filtered data
        first_penance_time = filtered_chart_df['Completion_Time'].min()
        last_penance_time = filtered_chart_df['Completion_Time'].max()
        total_completed_in_range = len(filtered_chart_df)
        total_score_in_range = filtered_chart_df['Score'].sum() if 'Score' in filtered_chart_df.columns else 0

        first_str = first_penance_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(first_penance_time) else "N/A"
        last_str = last_penance_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(last_penance_time) else "N/A"

        _chart_stats = mo.hstack([
            mo.stat(label="First in Range", value=first_str, bordered=True),
            mo.stat(label="Last in Range", value=last_str, bordered=True),
            mo.stat(label="Completed in Range", value=str(total_completed_in_range), bordered=True),
            mo.stat(label="Total Score", value=str(total_score_in_range), bordered=True),
        ], widths="equal", align="center")
    else:
        _chart_output = mo.md("_No data matches the selected filters._").callout(kind="warn")
        _chart_stats = None

    mo.vstack([_chart_output, _chart_stats] if _chart_stats else [_chart_output])
    return


@app.cell
def _(mo, penances_df):
    # Class mapping for table
    _class_mapping = {
        'veteran': 'Veteran',
        'zealot': 'Zealot',
        'zelot': 'Zealot',
        'psyker': 'Psyker',
        'ogryn': 'Ogryn',
        'adamant': 'Arbitrator',
        'broker': 'Hive Scum'
    }

    def _extract_class(achievement_id):
        achievement_id_lower = achievement_id.lower()
        for class_key, class_value in _class_mapping.items():
            if class_key in achievement_id_lower:
                return class_value
        return 'General'

    # Add class column and Penance_Category to dataframe
    table_df = penances_df.copy()
    table_df['Penance_Class'] = table_df['Achievement_ID'].apply(_extract_class)

    # Map raw Category to friendly category names
    _category_map = {
        'loc_achievement_category_account_label': 'Account',
        'loc_class_abilities_title': 'Class',
        'loc_class_progression_title': 'Class',
        'loc_achievement_category_offensive_label': 'Tactical',
        'loc_achievement_category_defensive_label': 'Tactical',
        'loc_achievement_category_teamplay_label': 'Tactical',
        'loc_achievement_category_heretics_label': 'Heretical',
        'loc_achievement_subcategory_missions_general_label': 'Missions - General',
        'loc_achievement_subcategory_missions_auric_label': 'Missions - General',
        'loc_achievement_subcategory_missions_havoc_label': 'Missions - Havoc',
        'loc_achievement_subcategory_missions_survival_label': 'Missions - General',
        'loc_achievement_subcategory_twins_mission_label': 'Exploration',
        'loc_weapon_progression_mastery': 'Weapons',
        'loc_achievement_category_weapons_label': 'Weapons',
    }

    # Exploration detection via Achievement_ID patterns
    _exploration_terms = ['group_mission_zone_wide', 'collectible', 'destructible', 'mission_zone_',
                          'mission_scavenge_samples', 'mission_propaganda_fan_kills', 'mission_raid_bottles']
    _exploration_regex = '|'.join(_exploration_terms)

    def _map_category(row):
        if row['Category'] in _category_map:
            return _category_map[row['Category']]
        if row['Achievement_ID'] and any(term in row['Achievement_ID'].lower() for term in _exploration_terms):
            return 'Exploration'
        return 'Endeavours'

    table_df['Penance_Category'] = table_df.apply(_map_category, axis=1)
    table_df = table_df.sort_values(by='PROGRESS_DIFF', ascending=True)

    # Create calculated columns for progress display
    def _make_progress_bar(v):
        if isinstance(v, str):
            v = float(v.rstrip("%")) / 100.0
        display_v = min(v, 1.0)
        blocks = int(display_v * 10)
        return "█" * blocks + "░" * (10 - blocks)

    def _format_percentage(v):
        if isinstance(v, str):
            v = float(v.rstrip("%")) / 100.0
        return f"{v*100:.0f}%"

    table_df['PROGRESS'] = table_df['Progress_Percentage'].apply(_format_percentage)
    table_df['PROGRESS_BAR'] = table_df['Progress_Percentage'].apply(_make_progress_bar)

    # Count in-progress penances per category and class
    _in_progress_df = table_df[table_df['Status'] == 'In Progress']
    _cat_counts = _in_progress_df['Penance_Category'].value_counts().to_dict()
    _class_counts = _in_progress_df['Penance_Class'].value_counts().to_dict()
    _total_in_progress = len(_in_progress_df)

    # Filter dropdowns with counts
    status_filter = mo.ui.dropdown(
        options=["All", "In Progress", "Completed"],
        value="All",
        label="Status"
    )

    _categories = ["Account", "Class", "Tactical", "Heretical", "Missions - General", "Missions - Havoc", "Exploration", "Endeavours", "Weapons"]
    _category_options = {"All": "All"} | {f"{cat} ({_cat_counts.get(cat, 0)})": cat for cat in _categories}
    category_filter = mo.ui.dropdown(
        options=_category_options,
        value="All",
        label="Category"
    )

    _classes = ["General", "Arbitrator", "Hive Scum", "Ogryn", "Psyker", "Veteran", "Zealot"]
    _class_options = {"All": "All"} | {f"{cls} ({_class_counts.get(cls, 0)})": cls for cls in _classes}
    class_filter = mo.ui.dropdown(
        options=_class_options,
        value="All",
        label="Class"
    )

    mo.vstack([
        mo.md("#### ::lucide:table:: Penance Data"),
        mo.hstack([status_filter, category_filter, class_filter], justify="start", gap=1)
    ])
    return category_filter, class_filter, status_filter, table_df


@app.cell(hide_code=True)
def _(category_filter, class_filter, mo, status_filter, table_df):
    # Apply filters
    filtered_df = table_df.copy()

    if status_filter.value != "All":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter.value]

    if category_filter.value != "All":
        filtered_df = filtered_df[filtered_df['Penance_Category'] == category_filter.value]

    if class_filter.value != "All":
        filtered_df = filtered_df[filtered_df['Penance_Class'] == class_filter.value]

    # Style function for percentage and bar coloring
    def _style_progress(row_id, column_name, value):
        if column_name not in ("PROGRESS", "PROGRESS_BAR"):
            return {}
        if isinstance(value, str):
            if "%" in value:
                value = float(value.rstrip("%")) / 100.0
            else:
                value = value.count("█") / 10.0
        if value >= 0.8:
            return {"color": "#22c55e"}
        elif value >= 0.5:
            return {"color": "#f97316"}
        else:
            return {"color": "#ef4444"}

    _display_cols = ["Title", "Description", "Score", "Penance_Class", "Penance_Category", "Status", "Progress", "Goal", "Completion_Time", "PROGRESS", "PROGRESS_BAR"]
    _filtered_display = filtered_df[_display_cols].reset_index(drop=True)

    penance_table = mo.ui.table(
        _filtered_display,
        style_cell=_style_progress,
        page_size=15,
        selection="multi",
        wrapped_columns=['Description']
    )
    return (penance_table,)


@app.cell
def _(mo, pd, penance_table):
    # Selected penances tracker
    selected = penance_table.value

    if selected is not None and isinstance(selected, pd.DataFrame) and len(selected) > 0:
        _tracked_content = mo.ui.table(selected, page_size=10)
    else:
        _tracked_content = mo.md("_Select penances from the Penance List tab to track them here._").callout(kind="info")

    # Tabs
    mo.ui.tabs({
        "::lucide:list:: Penance List": penance_table,
        f"::lucide:target:: Tracked ({len(selected) if selected is not None and isinstance(selected, pd.DataFrame) else 0})": _tracked_content,
    })
    return


if __name__ == "__main__":
    app.run()
