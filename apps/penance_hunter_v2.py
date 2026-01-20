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
    return account_meta, completed_df, penances_df


@app.cell
def _(account_meta, completed_df, csv_upload, mo, penances_df):
    # Account info header
    account_name = penances_df['Export_Account'].iloc[0] if 'Export_Account' in penances_df.columns else "Unknown"
    character_name = penances_df['Export_Character'].iloc[0] if 'Export_Character' in penances_df.columns else "Unknown"

    total_penances = len(penances_df)
    total_completed = len(completed_df)
    completion_pct = round(total_completed / total_penances * 100, 1)

    _stats = [
        mo.stat(label="Total Penances", value=total_penances, bordered=True),
        mo.stat(label="Completed", value=total_completed, bordered=True),
        mo.stat(label="Completion %", value=f"{completion_pct}%", bordered=True),
        mo.stat(label="Account Level", value=account_meta.get('account_level', 'N/A'), bordered=True),
        mo.stat(label="Prestige", value=account_meta.get('prestige', 'N/A'), bordered=True),
    ]

    _header = mo.md(f"### ::lucide:user:: **{account_name}** - {character_name}")

    mo.vstack([
        _header,
        mo.hstack(_stats, widths="equal", align="center"),
        csv_upload,
    ])
    return


@app.cell(hide_code=True)
def _(mo, penances_df):
    # Class mapping for filtering
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

    penances_df['Penance_Class'] = penances_df['Achievement_ID'].apply(extract_class)

    # Get unique classes for dropdown
    available_classes = ['All'] + sorted(penances_df['Penance_Class'].unique().tolist())

    class_filter = mo.ui.dropdown(
        options=available_classes,
        value='All',
        label="::lucide:filter:: Class"
    )

    status_filter = mo.ui.dropdown(
        options=['All', 'Completed', 'In Progress'],
        value='All',
        label="::lucide:filter:: Status"
    )

    mo.hstack([class_filter, status_filter]).left()
    return class_filter, status_filter


@app.cell(hide_code=True)
def _(class_filter, penances_df, status_filter):
    # Apply filters
    filtered_df = penances_df.copy()

    if class_filter.value != 'All':
        filtered_df = filtered_df[filtered_df['Penance_Class'] == class_filter.value]

    if status_filter.value != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == status_filter.value]

    filtered_df = filtered_df.sort_values(by='PROGRESS_DIFF', ascending=True)
    return (filtered_df,)


@app.cell(hide_code=True)
def _(class_filter, filtered_df, mo, status_filter):
    # Summary stats for filtered view
    _filtered_total = len(filtered_df)
    _filtered_completed = len(filtered_df[filtered_df['Status'] == 'Completed'])
    _filtered_in_progress = len(filtered_df[filtered_df['Status'] == 'In Progress'])
    _filtered_pct = round(_filtered_completed / _filtered_total * 100, 1) if _filtered_total > 0 else 0

    _filter_label = f"{class_filter.value}" if class_filter.value != 'All' else "All Classes"
    if status_filter.value != 'All':
        _filter_label += f" ({status_filter.value})"

    _cards = [
        mo.stat(label="Showing", value=_filtered_total, bordered=True),
        mo.stat(label="Completed", value=_filtered_completed, bordered=True),
        mo.stat(label="In Progress", value=_filtered_in_progress, bordered=True),
        mo.stat(label="Completion", value=f"{_filtered_pct}%", bordered=True),
    ]

    mo.vstack([
        mo.md(f"### {_filter_label}"),
        mo.hstack(_cards, widths="equal", align="center"),
    ])
    return


@app.cell(hide_code=True)
def _(alt, completed_df, mo, penances_df):
    # Cumulative completion chart
    _cumulative_chart = alt.Chart(completed_df).mark_line(point=True).encode(
        x=alt.X('Completion_Time:T', title='Date'),
        y=alt.Y('CUMULATIVE_COUNT:Q', title='Total Completed'),
        tooltip=[
            alt.Tooltip('Completion_Time:T', title='Date'),
            alt.Tooltip('Title:N', title='Penance'),
            alt.Tooltip('CUMULATIVE_COUNT:Q', title='Total'),
        ]
    ).properties(
        width="container",
        height=300,
        title='Penance Completion Progress'
    ).interactive()

    # Class breakdown chart
    class_summary = penances_df.groupby(['Penance_Class', 'Status']).size().reset_index(name='count')

    _class_chart = alt.Chart(class_summary).mark_bar().encode(
        x=alt.X('Penance_Class:N', title='Class'),
        y=alt.Y('count:Q', title='Count'),
        color=alt.Color('Status:N', scale=alt.Scale(
            domain=['Completed', 'In Progress'],
            range=['#22c55e', '#f97316']
        )),
        tooltip=['Penance_Class', 'Status', 'count']
    ).properties(
        width="container",
        height=300,
        title='Penances by Class'
    )

    cumulative_chart = mo.ui.altair_chart(_cumulative_chart, chart_selection=False)
    class_chart = mo.ui.altair_chart(_class_chart, chart_selection="point")

    mo.ui.tabs({
        "::lucide:chart-line:: Progress": cumulative_chart,
        "::lucide:chart-bar:: By Class": class_chart,
    })
    return


@app.cell(hide_code=True)
def _(filtered_df, mo):
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
    _table_df = filtered_df[_display_cols].reset_index(drop=True)

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
