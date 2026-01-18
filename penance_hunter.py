# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "marimo",
#     "pandas==2.3.3",
#     "polars==1.37.1",
#     "pyarrow",
#     "pyfiglet==1.0.4",
#     "pyzmq",
# ]
# ///

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="full", layout_file="layouts/penance_hunter.grid.json")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import datetime, re
    import altair as alt
    import polars as pl
    import pyfiglet
    from pathlib import Path
    import io
    return alt, io, mo, pd, pyfiglet, re


@app.cell
def _(mo, pyfiglet):
    nurgle_ascii = pyfiglet.figlet_format("Penance Hunter", font="bloody", width=200)
    penance_title =  pyfiglet.figlet_format(f"{' '*20}notebook visualizer 40k", font="double_blocky", width=200)

    with mo.redirect_stdout():
        print(nurgle_ascii)
        print(penance_title)
        print()
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    """)
    return


@app.cell
def _(mo):
    csv_upload = mo.ui.file(
        filetypes=[".csv"],  # only allow CSVs
        multiple=False,
        kind="button",       # or "area" for drag-and-drop
        label="select your penance export csv",
    )
    csv_upload
    return (csv_upload,)


@app.cell
def _(csv_upload, io, pd, re):
    penance_export = csv_upload
    penances_df = pd.DataFrame()

    print("~ now reading file: ", penance_export.name())
    penances_df = pd.read_csv(io.BytesIO(penance_export.contents()), comment='#')
    penances_df['Completion_Time'] = pd.to_datetime(penances_df['Completion_Time'], errors='coerce')
    penances_df['EXPORT_FILE'] = penance_export.name()
    penances_df['EXPORT_FILE'] = penances_df['EXPORT_FILE'].astype(str)

    # Updated regex to match Account ID (UUID format)
    match = re.search(r'[0-9a-f-]+_([0-9]{8})_[0-9]{6}\.csv', str(penance_export.name()))
    ts_match = re.search(r'[0-9a-f-]+_([0-9]{8})_([0-9]{6})\.csv', str(penance_export.name()))

    if ts_match:

        # Join the two parts: 20230515_123045 → 20230515123045
        ts_string = ts_match.group(1) + ts_match.group(2)
        # Convert to pandas datetime (nanoseconds resolution by default)
        penances_df['EXPORT_TS'] = pd.to_datetime(
            ts_string,
            format='%Y%m%d%H%M%S',   # matches 20230515123045
            errors='coerce'          # → NaT if parsing fails
        )
    else:
        # Pattern didn't match – keep as missing datetime
        penances_df['EXPORT_TS'] = pd.NaT

    penances_df['EXPORT_DATE'] = match.group(1).title() if match else "Unknown"
    penances_df = penances_df.sort_values('Completion_Time')
    penances_df["Cumulative_Count"] = range(1, len(penances_df) + 1)
    penances_df['PROGRESS_DIFF'] = penances_df['Goal'] - penances_df['Progress']

    penances_df = penances_df.sort_values(by='PROGRESS_DIFF', ascending=True)

    print(f"~ created dataframe from penance export ({len(penances_df)} rows)")

    completed_df = penances_df[penances_df['Status'] == 'Completed'].copy()
    completed_df['Completion_Time'] = pd.to_datetime(completed_df['Completion_Time'])
    completed_df['Completion_Date'] = completed_df['Completion_Time'].dt.date
    print(f"~ created dataframe of completed penances ({len(completed_df)} rows)")

    active_df = penances_df[penances_df['Status'] == 'In Progress'].copy()
    active_df = active_df.sort_values(by='Progress_Percentage', ascending=False)
    print(f"~ created dataframe of in-progess penances ({len(active_df)} rows)")
    return active_df, completed_df, penance_export, penances_df


@app.cell
def _(io, mo, pd, penance_export, penances_df):

    class_mapping = {
        'veteran': 'Veteran',
        'zealot': 'Zealot',
        'zelot': 'Zealot',
        'psyker': 'Psyker',
        'ogryn': 'Ogryn',
        'adamant': 'Arbitrator',
        'broker': 'Hive Scum'
    }

    # Function to extract class from Achievement_ID
    def extract_class(achievement_id):
      achievement_id_lower = achievement_id.lower()
      for class_key, class_value in class_mapping.items():
          if class_key in achievement_id_lower:
              return class_value
      return 'Unknown'

    def get_account_metadata(csv_upload):
        """Extract account metadata from CSV comments"""
        contents = csv_upload.contents()
        if contents is None:
            return None

        meta = {
            'all_characters': []
        }

        in_characters_section = False

        with io.TextIOWrapper(io.BytesIO(contents), encoding="utf-8") as f:
            for line in f:
                if not line.startswith('#'):
                    break

                line_stripped = line.lstrip('#').strip()

                # Check if we're entering the All Characters section
                if 'All Characters:' in line_stripped:
                    in_characters_section = True
                    continue

                # If in characters section, collect character lines
                if in_characters_section:
                    # Check if line starts with a number (character entry)
                    if line_stripped and line_stripped[0].isdigit():
                        meta['all_characters'].append(line_stripped)
                    # Empty line or new section ends character list
                    elif not line_stripped or 'Export Character:' in line_stripped:
                        in_characters_section = False

                # Parse other metadata
                if 'Account ID:' in line_stripped:
                  meta['account_id'] = line_stripped.split(':', 1)[1].strip()
                elif 'Account Level:' in line_stripped:
                  meta['account_level'] = int(line_stripped.split(':')[1].strip())
                elif 'Account True Level:' in line_stripped:
                  meta['account_true_level'] = int(line_stripped.split(':')[1].strip())
                elif 'Number of Characters:' in line_stripped:
                  meta['num_characters'] = int(line_stripped.split(':')[1].strip())
                elif 'Export Prestige:' in line_stripped:
                  meta['prestige'] = int(line_stripped.split(':')[1].strip())
        return meta

    class_df = penances_df[penances_df['Category'].isin(['loc_class_abilities_title',
                                                         'loc_class_progression_title'])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    account_df = penances_df[penances_df['Category'].isin(['loc_achievement_category_account_label'])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    tactical_df = penances_df[penances_df['Category'].isin(['loc_achievement_category_offensive_label',
                                                            'loc_achievement_category_defensive_label',
                                                            'loc_achievement_category_teamplay_label'
                                                           ])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    heretical_df = penances_df[penances_df['Category'].isin(['loc_achievement_category_heretics_label'])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    missions_df = penances_df[penances_df['Category'].isin(['loc_achievement_subcategory_missions_general_label',
                                                            'loc_achievement_subcategory_missions_auric_label',
                                                            'loc_achievement_subcategory_missions_havoc_label',
                                                            'loc_achievement_subcategory_missions_survival_label'
                                                           ])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    exploration_terms = ['group_mission_zone_wide',
                        'collectible',
                        'destructible',
                        'mission_zone_',
                        'mission_scavenge_samples',
                        'mission_propaganda_fan_kills',
                        'mission_raid_bottles']

    exploration_regex = '|'.join(exploration_terms)


    # Filter DataFrame
    exploration_df = penances_df[
        (penances_df['Achievement_ID'].str.contains(exploration_regex, case=False, na=False)) |
        (penances_df['Category'].isin(['loc_achievement_subcategory_twins_mission_label']))
    ].sort_values(by='PROGRESS_DIFF', ascending=True).copy()



    weapons_df = penances_df[penances_df['Category'].isin(['loc_weapon_progression_mastery',
                                                           'loc_achievement_category_weapons_label'
                                                          ])].sort_values(by='PROGRESS_DIFF', ascending=True).copy() 

    leftover_df = penances_df[~penances_df['Category'].isin(['loc_class_abilities_title',
                                                             'loc_class_progression_title',
                                                             'loc_achievement_category_account_label',
                                                             'loc_achievement_category_offensive_label',
                                                             'loc_achievement_category_defensive_label',
                                                             'loc_achievement_category_teamplay_label',
                                                             'loc_achievement_category_heretics_label',
                                                             'loc_achievement_subcategory_missions_general_label',
                                                             'loc_achievement_subcategory_missions_auric_label',
                                                             'loc_achievement_subcategory_missions_havoc_label',
                                                             'loc_achievement_subcategory_missions_survival_label',
                                                             'loc_achievement_subcategory_twins_mission_label',
                                                             'loc_weapon_progression_mastery',
                                                             'loc_achievement_category_weapons_label'
                                                            ])].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    leftover_df = leftover_df[~leftover_df['Achievement_ID'].str.contains(exploration_regex, case=False, na=False)].sort_values(by='PROGRESS_DIFF', ascending=True).copy()

    with mo.redirect_stdout():

        current_date = pd.Timestamp.now().replace(microsecond=0)

        print(f" -- {str(current_date)} --")

        print(f"  loading penances for completion tracking from export_file --> {penance_export.name()}\n")

        print(f"\n\n  - Export details -")

        #for cls, count in (penances_df['Status'].value_counts(dropna=False).items()):
        #    print(f"   {cls:<10} {count:>5}")

         # Get metadata
        meta = get_account_metadata(penance_export)

        # Enhanced print output
        print(f"\n    exported by: {penances_df['Export_Character'].unique()[0]} ({penances_df['Export_Account'].unique()[0]})")
        print(f"    account ID: {meta.get('account_id', 'N/A')}")
        print(f"    export platform: {penances_df['Export_Platform'].unique()[0]}")

        # All Characters
        print(f"\n    all characters:")
        for char_line in meta.get('all_characters', []):
            print(f"      {char_line}")

        # Account-wide stats (with prestige)
        print(f"\n    account level: {meta.get('account_level', 'N/A')} (true: {meta.get('account_true_level', 'N/A')}, prestige: {meta.get('prestige', 'N/A')})")

        # Export info
        print(f"\n    export time: {str(penances_df['EXPORT_TS'].unique()[0])}")
        print(f"    total completed penances: {len(penances_df[penances_df['Status']=='Completed'])}/{len(penances_df)} ({round(len(penances_df[penances_df['Status']=='Completed'])/len(penances_df),3)*100:.1f}%)")
        print(f"    earliest completed penance: {penances_df[penances_df['Status']=='Completed']['Completion_Time'].min()}")
        print(f"    most recently completed penance: {penances_df[penances_df['Status']=='Completed']['Completion_Time'].max()}")

        print(f"\n\n{'x'*200}\n\n")

        print(f"  create dataframes per in-game mapped category:\n")

        print(f"\n\n  - 1. Account Penances -")
        for cls, count in (account_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 2. Class Penances -")

        class_df['Penance_Class'] = class_df['Achievement_ID'].apply(extract_class)

        class_summary = (
            class_df
                .groupby('Penance_Class', dropna=False)['Status']
                .agg(
                    total='size',
                    completed=lambda s: (s == 'Completed').sum()
                ).astype({'total': int, 'completed': int})
        )


        class_summary['pct'] = class_summary['completed'] / class_summary['total']

        class_df = class_df.sort_values('Completion_Time')
        class_df['Cumulative_Count_Per_Class'] = class_df.groupby('Penance_Class').cumcount() + 1
        last_points = class_df.groupby('Penance_Class').last().reset_index()



        for cls, row in class_summary.sort_index().iterrows():
            completed = int(row.completed)
            total = int(row.total)
            print(
                f"   {cls:<12} {completed}/{total} ({row.pct:.0%})"
            )

        print(f"\n\n  - 3. Tactical Penances -")
        for cls, count in (tactical_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 4. Heretical Penances -")
        for cls, count in (heretical_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 5. Missions Penances -")
        for cls, count in (missions_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 6. Exploration Penances -")
        for cls, count in (exploration_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 7. Endeavours Penances -")
        for cls, count in (leftover_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        print(f"\n\n  - 8. Weapons Penances -")
        for cls, count in (weapons_df['Status'].value_counts(dropna=False).items()):
            print(f"   {cls:<10} {count:>5}")

        # adjust current date for better visual presentation
        current_date = pd.Timestamp.now() + pd.Timedelta(days=5)
    return (
        class_df,
        current_date,
        exploration_df,
        last_points,
        missions_df,
        tactical_df,
    )


@app.cell
def _(active_df, class_df, exploration_df, missions_df, mo, tactical_df):
    def progress_text(v):
        # v might be "98%" or 0.98
        if isinstance(v, str):
            v = float(v.rstrip("%")) / 100.0
        blocks = int(v * 10)
        return f"{v*100:.0f}% " + "█" * blocks

    def style_cell(_row_id, column_name, value):
        if column_name != "Progress_Percentage":
            return {}
        # choose color based on value if you like
        if isinstance(value, str):
            value = float(value.rstrip("%")) / 100.0
        color = "green" if value >= 0.8 else "orange" if value >= 0.5 else "red"
        return {"color": color}

    def build_table(df,pagesize):
        penance_table = mo.ui.table(
            df[["Title", "Description","Achievement_ID", "Progress", "Goal", "PROGRESS_DIFF", "Progress_Percentage"]].reset_index(drop=True),
            format_mapping={"Progress_Percentage": progress_text},
            style_cell=style_cell,
            page_size=pagesize,
            wrapped_columns=['Description']
        )
        return penance_table

    active_df['PROGRESS_DIFF'] = active_df['Goal'] - active_df['Progress']

    active_exploration_df = active_df[active_df["Achievement_ID"].isin(exploration_df["Achievement_ID"])].sort_values(by='PROGRESS_DIFF', ascending=True)
    active_havoc_df = active_df[active_df["Achievement_ID"].str.contains("havoc")].sort_values(by='PROGRESS_DIFF', ascending=True)
    active_class_df = active_df[active_df["Achievement_ID"].isin(class_df["Achievement_ID"])].sort_values(by='PROGRESS_DIFF', ascending=True)
    active_tactical_df = active_df[active_df["Achievement_ID"].isin(tactical_df["Achievement_ID"])].sort_values(by='PROGRESS_DIFF', ascending=True)
    active_missions_df = active_df[active_df["Achievement_ID"].isin(missions_df["Achievement_ID"]) & ~active_df["Achievement_ID"].isin(active_havoc_df["Achievement_ID"])].sort_values(by='PROGRESS_DIFF', ascending=True)

    in_progress_table = build_table(active_df,2)
    havoc_table = build_table(active_havoc_df,5)
    exploration_table = build_table(active_exploration_df,100)
    tactical_table = build_table(active_tactical_df,100)
    missions_table = build_table(active_missions_df,100)
    class_table = build_table(active_class_df,100)

    in_progress_page = mo.vstack([mo.md("### In Progress Penances"),
               mo.md("#### Class"),
               class_table,
               mo.md("#### Tactical"),
               tactical_table,
               mo.md("#### Misions"),
               missions_table,
               mo.md("#### Exploration"),
               exploration_table,
               mo.md("#### Havoc"),
               havoc_table,
               mo.md("#### All"),
               in_progress_table,
              ])
    return (
        class_table,
        exploration_table,
        havoc_table,
        in_progress_page,
        in_progress_table,
        missions_table,
        progress_text,
        style_cell,
        tactical_table,
    )


@app.cell
def _(
    class_table,
    exploration_table,
    havoc_table,
    in_progress_table,
    missions_table,
    mo,
    pd,
    progress_text,
    style_cell,
    tactical_table,
):
    selected_penances = [
        t.value
        for t in [class_table,
                  havoc_table,
                  exploration_table,
                  in_progress_table,
                  tactical_table,
                  missions_table
                 ]
        if t.value is not None and len(t.value) > 0
    ]

    selected_df = pd.concat(selected_penances, ignore_index=True) if selected_penances else pd.DataFrame()

    selected_table = mo.ui.table(selected_df,
                                 selection="multi",
                                 format_mapping={"Progress_Percentage": progress_text},
                                 style_cell=style_cell,
                                 page_size=10)

    tracked_page = mo.vstack([mo.md("### TRACKED PENANCES"),selected_table])
    return (tracked_page,)


@app.cell
def _(completed_page, in_progress_page, mo, tracked_page):
    tabs = mo.ui.tabs({
        "Completed": completed_page,
        "In Progress": in_progress_page,
        "Tracked": tracked_page,
    })

    tabs
    return


@app.cell
def _(class_progression_chart, completed_df, cumulative_chart, mo):
    completed_page = mo.vstack([mo.md("---"),mo.md("### Completed Penances"),mo.ui.table(completed_df),cumulative_chart,class_progression_chart])
    return (completed_page,)


@app.cell
def _(alt, class_df, completed_df, current_date, last_points, mo):
    # Create interactive Altair chart - Cumulative completions over time
    cumulative_chart = alt.Chart(completed_df).mark_line(point=True).encode(
      x=alt.X('Completion_Time:T', title='Completion Date'),
      y=alt.Y('Cumulative_Count:Q', title='Total Penances Completed'),
      tooltip=[
          alt.Tooltip('Completion_Time:T', title='Date'),
          alt.Tooltip('Title:N', title='Penance'),
          alt.Tooltip('Cumulative_Count:Q', title='Total Completed'),
          alt.Tooltip('Score:Q', title='Score')
      ]
    ).properties(
      width="container",
      height=400,
      title='Cumulative Penance Completions Over Time'
    ).interactive()

    # Create cumulative chart by penance class
    class_progression_chart = alt.Chart(class_df).mark_line(point=True).encode(
      x=alt.X('Completion_Time:T', title='Date'),
      y=alt.Y('Cumulative_Count_Per_Class:Q', title='Operative Penances Completed'),
      color=alt.Color('Penance_Class:N', title='Class'),
      tooltip=[
          alt.Tooltip('Penance_Class:N', title='Class'),
          alt.Tooltip('Completion_Time:T', title='Date'),
          alt.Tooltip('Cumulative_Count_Per_Class:Q', title='Total for this class'),
          alt.Tooltip('Title:N', title='Penance')
      ]
    ).properties(
      width=2200,
      height=400,
      title='Operative Penance Progression by Class'
    ).interactive()

    # Create the line chart
    line_chart = alt.Chart(class_df).mark_line(point=True).encode(
      x=alt.X('Completion_Time:T', title='Date', scale=alt.Scale(domain=[class_df['Completion_Time'].min(), current_date])),
      y=alt.Y('Cumulative_Count_Per_Class:Q', title='Operative Penances Completed'),
      color=alt.Color('Penance_Class:N', title='Class'),
      tooltip=[
          alt.Tooltip('Penance_Class:N', title='Class'),
          alt.Tooltip('Completion_Time:T', title='Date'),
          alt.Tooltip('Cumulative_Count_Per_Class:Q', title='Total for this class'),
          alt.Tooltip('Title:N', title='Penance')
      ]
    )

    # Create the last points layer with larger markers
    last_points_chart = alt.Chart(last_points).mark_point(size=200, filled=True).encode(
      x=alt.X('Completion_Time:T', scale=alt.Scale(domain=[class_df['Completion_Time'].min(), current_date])),
      y=alt.Y('Cumulative_Count_Per_Class:Q'),
      color=alt.Color('Penance_Class:N', title='Class'),
      tooltip=[
          alt.Tooltip('Penance_Class:N', title='Class'),
          alt.Tooltip('Completion_Time:T', title='Date'),
          alt.Tooltip('Cumulative_Count_Per_Class:Q', title='Total for this class')
      ]
    )

    # Layer them together
    class_progression_chart = (
        line_chart + last_points_chart
    ).properties(
        width="container",   # fills the page/container width
        height=400,
        title="Operative Penance Progression by Class",
    ).interactive()

    class_progression_chart = mo.ui.altair_chart(class_progression_chart)

    cumulative_chart = mo.ui.altair_chart(cumulative_chart)
    return class_progression_chart, cumulative_chart


@app.cell
def _(class_progression_chart, cumulative_chart, mo):
    mo.vstack([cumulative_chart,class_progression_chart])
    return


if __name__ == "__main__":
    app.run()
