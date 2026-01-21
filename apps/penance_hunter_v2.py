# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "marimo",
#     "pandas==2.3.3",
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
        footer=mo.md("_For the Emperor!_"),
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
                elif 'Export Prestige:' in line_stripped:
                    meta['prestige'] = int(line_stripped.split(':')[1].strip())
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

    # Format timestamps
    export_time_str = export_timestamp.strftime('%Y-%m-%d %H:%M') if not export_timestamp != export_timestamp else "Unknown"
    earliest_str = earliest_completion.strftime('%Y-%m-%d') if not earliest_completion != earliest_completion else "N/A"
    latest_str = latest_completion.strftime('%Y-%m-%d') if not latest_completion != latest_completion else "N/A"

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
            # Parse: "1. glowm (Zealot) - Level 30 (True: 169, +139)" or "2. Zek (Hive Scum) - Level 30"
            char_match = _re.match(r'\d+\.\s*(.+?)\s*\(([^)]+)\)\s*-\s*Level\s*(\d+)(?:\s*\(True:\s*(\d+),\s*\+(\d+)\))?', char)
            if char_match:
                name, cls, level, true_level, bonus = char_match.groups()
                # Map class names (adamant -> Arbitrator, broker -> Hive Scum)
                display_cls = _class_mapping.get(cls.lower(), cls.title())
                if true_level and bonus:
                    caption = f"Level {level} (True: {true_level}, +{bonus})"
                else:
                    caption = f"Level {level}"
                _char_stats.append(mo.stat(label=display_cls, caption=caption, value=name, bordered=True))
            else:
                _char_stats.append(mo.stat(label="Unknown", value=char, bordered=True))
        _char_section = mo.accordion({"::lucide:users:: Operatives": mo.hstack(_char_stats, wrap=True)})
    else:
        _char_section = None

    _header = mo.md(f"### **{account_name}** - exported by {character_name}")

    _content = [
        _header,
        mo.hstack(_stats, widths="equal", align="center"),
        mo.hstack(_time_stats, widths="equal", align="center"),
    ]
    if _char_section:
        _content.append(_char_section)

    mo.vstack(_content)
    return


@app.cell(hide_code=True)
def _(alt, completed_df, mo, pd):
    # Class mapping for extracting class from Achievement_ID
    class_mapping = {
        'veteran': 'Veteran',
        'zealot': 'Zealot',
        'zelot': 'Zealot',
        'psyker': 'Psyker',
        'ogryn': 'Ogryn',
        'adamant': 'Arbitrator',
        'broker': 'Hive Scum'
    }

    def extract_class(achievement_id):
        achievement_id_lower = achievement_id.lower()
        for class_key, class_value in class_mapping.items():
            if class_key in achievement_id_lower:
                return class_value
        return 'General'

    # Add class to completed penances
    chart_df = completed_df.copy()
    chart_df['Penance_Class'] = chart_df['Achievement_ID'].apply(extract_class)

    # Sort by completion time and calculate cumulative count per class
    chart_df = chart_df.sort_values('Completion_Time')
    chart_df['CCOUNT_PER_CLASS'] = chart_df.groupby('Penance_Class').cumcount() + 1

    # Get last point for each class (for endpoint markers)
    last_points = chart_df.groupby('Penance_Class').last().reset_index()

    # Extend x-axis slightly past last completion
    current_date = pd.Timestamp.now() + pd.Timedelta(days=5)

    # Line chart for progression
    line_chart = alt.Chart(chart_df).mark_line(point=True).encode(
        x=alt.X('Completion_Time:T', title='Date', scale=alt.Scale(domain=[chart_df['Completion_Time'].min(), current_date])),
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
        x=alt.X('Completion_Time:T', scale=alt.Scale(domain=[chart_df['Completion_Time'].min(), current_date])),
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

    mo.ui.altair_chart(class_progression_chart, chart_selection=False)
    return


@app.cell(hide_code=True)
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

    # Add class column to dataframe
    table_df = penances_df.copy()
    table_df['Penance_Class'] = table_df['Achievement_ID'].apply(_extract_class)
    table_df = table_df.sort_values(by='PROGRESS_DIFF', ascending=True)

    # Progress table with formatting
    def progress_bar(v):
        if isinstance(v, str):
            v = float(v.rstrip("%")) / 100.0
        blocks = int(v * 10)
        return f"{v*100:.0f}% " + "█" * blocks + "░" * (10 - blocks)

    def style_progress(row_id, column_name, value):
        if column_name != "Progress_Percentage":
            return {}
        if isinstance(value, str):
            value = float(value.rstrip("%")) / 100.0
        if value >= 0.8:
            return {"color": "#22c55e"}
        elif value >= 0.5:
            return {"color": "#f97316"}
        else:
            return {"color": "#ef4444"}

    _display_cols = ["Title", "Description", "Penance_Class", "Progress", "Goal", "Progress_Percentage", "Status"]
    _table_df = table_df[_display_cols].reset_index(drop=True)

    penance_table = mo.ui.table(
        _table_df,
        format_mapping={"Progress_Percentage": progress_bar},
        style_cell=style_progress,
        page_size=15,
        selection="multi",
        wrapped_columns=['Description']
    )

    mo.vstack([
        mo.md("### ::lucide:list:: Penance List"),
        penance_table,
    ])
    return (penance_table,)


@app.cell(hide_code=True)
def _(mo, pd, penance_table):
    # Selected penances tracker
    selected = penance_table.value

    if selected is not None and isinstance(selected, pd.DataFrame) and len(selected) > 0:
        _selected_count = len(selected)
        _selected_progress = selected['Progress'].sum()
        _selected_goal = selected['Goal'].sum()
        _selected_pct = round(_selected_progress / _selected_goal * 100, 1) if _selected_goal > 0 else 0

        mo.vstack([
            mo.md(f"### ::lucide:target:: Tracked ({_selected_count} selected)"),
            mo.hstack([
                mo.stat(label="Combined Progress", value=f"{_selected_progress}/{_selected_goal}", bordered=True),
                mo.stat(label="Combined %", value=f"{_selected_pct}%", bordered=True),
            ], widths="equal"),
            mo.ui.table(selected, page_size=10),
        ])
    else:
        mo.md("_Select penances from the table above to track them here._").callout(kind="info")
    return


if __name__ == "__main__":
    app.run()
