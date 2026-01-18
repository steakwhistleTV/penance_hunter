-- penance_exporter_localization.lua
return {
    mod_name = {
        en = "Penance Exporter"
    },
    mod_description = {
        en = "Export all penance data for current operative to CSV file with hotkey. Files saved to APPDATA/Fatshark/Darktide/penance_exporter/"
    },
    export_penances_keybind = {
        en = "Export Penances to CSV"
    },
    export_penances_keybind_description = {
        en = "Press this key to export all penance data for your current operative to a CSV file"
    },
    cmd_desc_export = {
        en = "Export all penance data for current operative to CSV file"
    },
    msg_no_player = {
        en = "No player found. Make sure you're in-game with a character loaded."
    },
    msg_no_profile = {
        en = "No character profile found. Make sure you have a character selected."
    },
    msg_starting_export = {
        en = "Starting penance export for %s (%s)..."
    },
    msg_export_success = {
        en = "Penances exported to %s! Total: %d penances, Completed: %d"
    },
    msg_export_failed = {
        en = "Failed to export penances: %s"
    },
    msg_mod_loaded = {
        en = "Penance Exporter"
    },
    msg_mod_loaded_suffix = {
        en = "loaded! Use '/export_penances' or keybind to export penance data."
    },
    notify_export_success = {
        en = "Successfully exported penances:"
    },
    notify_export_failed = {
        en = "Export failed:"
    },
    notify_no_data = {
        en = "Please open the Penance menu first!"
    },
    notify_profiles_not_cached = {
        en = "Visit character selection to load all character names"
    },
}
