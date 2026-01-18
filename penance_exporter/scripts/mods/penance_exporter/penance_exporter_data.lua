-- penance_exporter_data.lua
local mod = get_mod("penance_exporter")

return {
    name = mod:localize("mod_name"),
    description = mod:localize("mod_description"),
    is_togglable = false,
    options = {
        widgets = {
            {
                setting_id = "export_penances_keybind",
                type = "keybind",
                default_value = {"f9"},
                keybind_global = false,
                keybind_trigger = "pressed",
                keybind_type = "function_call",
                function_name = "export_penances_csv",
            }
        }
    }
}
