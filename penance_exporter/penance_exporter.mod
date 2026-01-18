-- penance_exporter.mod
return {
  run = function()
    fassert(rawget(_G, "new_mod"), "`penance_exporter` encountered an error loading the Darktide Mod Framework.")
    new_mod("penance_exporter", {
      mod_script       = "penance_exporter/scripts/mods/penance_exporter/penance_exporter",
      mod_data         = "penance_exporter/scripts/mods/penance_exporter/penance_exporter_data",
      mod_localization = "penance_exporter/scripts/mods/penance_exporter/penance_exporter_localization",
    })
  end,
  packages = {},
}
