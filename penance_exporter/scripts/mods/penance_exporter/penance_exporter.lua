-- penance_exporter.lua
local mod = get_mod("penance_exporter")
local DMF = get_mod("DMF")

-- Version info
local MOD_VERSION = "2.3.1"

-- File I/O setup (borrowed from Scrivener pattern)
local io_lib = DMF:persistent_table("_io")
if not io_lib.initialized then
    io_lib = DMF.deepcopy(Mods.lua.io)
    io_lib.initialized = true
end

local os_lib = DMF:persistent_table("_os")
if not os_lib.initialized then
    os_lib = DMF.deepcopy(Mods.lua.os)
    os_lib.initialized = true
end

-- Required game systems
local AchievementUIHelper = require("scripts/managers/achievements/utility/achievement_ui_helper")
local AchievementCategories = require("scripts/settings/achievements/achievement_categories")
local AchievementTypes = require("scripts/managers/achievements/achievement_types")
local StatDefinitions = require("scripts/managers/stats/stat_definitions")

-- Setup paths
local appdata = os_lib.getenv("APPDATA")
local mod_dir = appdata .. "/Fatshark/Darktide/penance_exporter"

-- Localization helper
local function loc(key)
    local v = mod:localize(key)
    if type(v) == "table" then
        v = v.en or ""
    end
    return v or ""
end

-- Platform icon definitions (from Darktide's font icons)
local PLATFORM_ICONS = {
    ["\xEE\x81\xAB"] = "Steam",   -- Steam icon
    ["\xEE\x81\xAC"] = "Xbox",    -- Xbox icon
    ["\xEE\x81\xB1"] = "PSN",     -- PlayStation icon
    ["\xEE\x81\xAF"] = "Unknown"  -- Unknown platform icon
}

-- Extract platform type from account name and return both
local function extract_platform(account_name)
    if not account_name then
        return "Unknown", ""
    end

    local platform = "Unknown"
    local clean_name = account_name

    -- Check for platform icon and extract it
    for icon, platform_name in pairs(PLATFORM_ICONS) do
        if string.find(clean_name, icon) then
            platform = platform_name
            -- Remove the icon and any trailing space
            clean_name = string.gsub(clean_name, icon .. " ", "")
            clean_name = string.gsub(clean_name, icon, "")
            break
        end
    end

    return platform, clean_name
end

-- Strip or convert platform icons to text labels (for other uses)
local function clean_platform_icons(str)
    if not str then return "" end
    str = tostring(str)

    -- Replace platform icons with text labels
    for icon, label in pairs(PLATFORM_ICONS) do
        str = string.gsub(str, icon .. " ", "[" .. label .. "] ")
        str = string.gsub(str, icon, "[" .. label .. "]")
    end

    return str
end

-- Game icon definitions (icons that appear in penance names/descriptions)
local GAME_ICONS = {
    ["\xEE\x80\x80"] = "(Private Only)",      -- Private lobby icon
    ["\xEE\x80\x81"] = "(Party)",             -- Party icon
    ["\xEE\x80\x82"] = "(Solo)",              -- Solo icon
    ["\xEE\x80\x83"] = "(Team)",              -- Team icon
    ["\xEE\x80\x84"] = "(Coop)",              -- Coop icon
    ["\xEE\x80\x85"] = "",                    -- Generic icon (empty replacement)
    ["\xEE\x80\x86"] = "",                    -- Level icon (empty replacement)
    ["\xEE\x80\x87"] = "(Auric)",             -- Auric icon
    ["\xEE\x80\x88"] = "(Maelstrom)",         -- Maelstrom icon
    ["\xEE\x81\x8F"] = "",                    -- Rank icon (empty replacement)
}

-- Replace game icons with descriptive text
local function replace_game_icons(str)
    if not str then return "" end
    str = tostring(str)

    -- Replace known game icons with text
    for icon, replacement in pairs(GAME_ICONS) do
        if replacement ~= "" then
            -- Add space before non-empty replacements
            str = string.gsub(str, icon, " " .. replacement)
        else
            -- Just remove empty replacements
            str = string.gsub(str, icon, "")
        end
    end

    -- Fallback: Remove any remaining icon font characters (UTF-8 Private Use Area E000-E8FF)
    -- Darktide uses \xEE\x80\x80 through \xEE\x83\xBF range for icon fonts
    str = string.gsub(str, "[\xEE][\x80-\x83][\x80-\xBF]", "")

    -- Clean up any double spaces created
    str = string.gsub(str, "  +", " ")
    -- Trim leading/trailing spaces
    str = string.gsub(str, "^%s+", "")
    str = string.gsub(str, "%s+$", "")

    return str
end

-- Strip Darktide formatting codes from text
local function strip_formatting_codes(str)
    if not str then return "" end
    str = tostring(str)
    -- Remove all {#...} formatting codes (color, reset, size, etc.)
    str = string.gsub(str, "{#[^}]*}", "")
    return str
end

-- CSV escape function to handle commas, quotes, and newlines
local function csv_escape(str)
    if not str then return '""' end
    str = tostring(str)
    -- Clean all icons and formatting codes before escaping
    str = clean_platform_icons(str)
    str = replace_game_icons(str)
    str = strip_formatting_codes(str)
    if string.find(str, '[",\n\r]') then
        str = string.gsub(str, '"', '""')
        return '"' .. str .. '"'
    end
    return str
end

-- Parse ISO8601 completion time to readable format
local function parse_completion_time(completion_time)
    if not completion_time or completion_time == 0 then
        return ""
    end

    if type(completion_time) == "string" then
        local year, month, day, hour, minute, second = completion_time:match("(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)")
        if year then
            local timestamp = os_lib.time({
                year = tonumber(year),
                month = tonumber(month),
                day = tonumber(day),
                hour = tonumber(hour),
                min = tonumber(minute),
                sec = tonumber(second),
            })
            return os_lib.date("%Y-%m-%d %H:%M:%S", timestamp)
        end
    end

    return tostring(completion_time)
end

-- Get archetype display name mapping
local function get_archetype_name(archetype)
    if not archetype then return "Unknown" end

    local archetype_names = {
        psyker = "Psyker",
        veteran = "Veteran",
        zealot = "Zealot",
        ogryn = "Ogryn"
    }

    return archetype_names[archetype.name] or archetype.display_name or archetype.name or "Unknown"
end

-- Store cached player and achievement data
local cached_player = nil
local cached_achievements_by_category = nil

-- Cache for character profiles (persists across views)
local cached_character_profiles = {}

-- Function to get current player safely
local function get_current_player()
    -- Try to get from local player manager first
    local player = Managers.player and Managers.player:local_player(1)
    if player then
        return player
    end

    -- If we have cached player data, use it
    if cached_player then
        return cached_player
    end

    return nil
end

-- Debug function to inspect available fields
local function debug_player_info()
    local player = get_current_player()
    if not player then
        mod:echo("DEBUG: No player found")
        return
    end

    mod:echo("=== DEBUG: Player Info ===")
    local account_id = player:account_id()
    local character_name = player:name()

    mod:echo(string.format("Account ID: %s", tostring(account_id)))
    mod:echo(string.format("Character name: %s", tostring(character_name)))

    -- Test social data service for account name
    local account_name = "Not found"
    if Managers.data_service and Managers.data_service.social and account_id then
        local player_info = Managers.data_service.social:get_player_info_by_account_id(account_id)
        if player_info then
            account_name = player_info:user_display_name() or "Unknown"
            mod:echo(string.format("Account name: %s", account_name))
        else
            mod:echo("player_info is nil - try opening Penance menu first")
        end
    else
        mod:echo("Managers.data_service.social not available")
    end

    local character_profile = player:profile()
    if character_profile then
        local archetype_name = get_archetype_name(character_profile.archetype)
        mod:echo(string.format("Archetype: %s", archetype_name))

        -- Explore profile fields
        mod:echo("=== Profile Fields ===")
        if character_profile.current_level then
            mod:echo(string.format("Current Level: %s", tostring(character_profile.current_level)))
        end
        if character_profile.current_xp then
            mod:echo(string.format("Current XP: %s", tostring(character_profile.current_xp)))
        end

        -- Try to get all characters and account level
        mod:echo("=== Account Info ===")

        -- Try Managers.account
        if Managers.account then
            mod:echo("Managers.account fields:")
            for k, v in pairs(Managers.account) do
                if type(v) ~= "function" then
                    mod:echo(string.format("  %s = %s", k, tostring(v)))
                end
            end
        end

        -- Try Managers.backend
        if Managers.backend and Managers.backend._account then
            mod:echo("Managers.backend._account exists")
            local backend_account = Managers.backend._account
            for k, v in pairs(backend_account) do
                if type(v) ~= "function" and not string.match(k, "^_") then
                    mod:echo(string.format("  %s = %s", k, tostring(v)))
                end
            end
        end

        -- Try backend progression (like true_level mod does)
        mod:echo("=== Backend Progression ===")
        if Managers.backend and Managers.backend.interfaces and Managers.backend.interfaces.progression then
            local progression_promise = Managers.backend.interfaces.progression:get_entity_type_progression("character")

            progression_promise:next(function(characters_progression)
                mod:echo(string.format("Number of characters: %d", #characters_progression))
                local account_level = 0

                for i, char_data in ipairs(characters_progression) do
                    local char_level = char_data.currentLevel or 0
                    account_level = account_level + char_level

                    -- Note: We don't have easy access to character name/archetype here
                    -- This data is in the profile, not progression
                    mod:echo(string.format("  %d. Character ID: %s - Level %d", i, char_data.id, char_level))
                end

                mod:echo(string.format("Account Level (sum of all character levels): %d", account_level))
            end):catch(function(error)
                mod:echo("Error fetching character progression: " .. tostring(error))
            end)
        else
            mod:echo("Backend progression interface not available")
        end

        -- Summary
        mod:echo("---")
        mod:echo(string.format("Summary: %s (%s) - %s", character_name, archetype_name, account_name))
    end
end

-- Forward declaration
local perform_export

-- Calculate true level from progression data (like true_level mod)
local function calculate_true_level(current_level, current_xp, xp_settings)
    if not xp_settings or not xp_settings.level_array then
        return nil, nil, nil
    end

    local level_array = xp_settings.level_array
    local total_xp = xp_settings.total_xp
    local max_level = xp_settings.max_level

    if current_level < max_level then
        -- Below max level, true level = current level
        return current_level, 0, 0
    else
        -- At or above max level, calculate true level
        local xp_per_level = level_array[max_level] - level_array[max_level - 1]
        local xp_over_max_level = current_xp - total_xp
        local additional_level = math.floor(xp_over_max_level / xp_per_level)
        local true_level = current_level + additional_level
        local prestige = math.floor(current_xp / total_xp)

        return true_level, additional_level, prestige
    end
end

-- Main function to export all penances for current operative to CSV
local function export_penances_csv()
    local player = get_current_player()
    if not player then
        mod:echo("msg_no_player")
        return
    end

    local character_profile = player:profile()
    if not character_profile then
        mod:echo("msg_no_profile")
        return
    end

    -- Get character name using player:name() (most reliable method)
    local character_name = player:name() or "Unknown"

    -- Get account name from social data service
    local account_name_raw = "Unknown"
    local account_id = player:account_id()

    if Managers.data_service and Managers.data_service.social and account_id then
        local player_info = Managers.data_service.social:get_player_info_by_account_id(account_id)
        if player_info then
            account_name_raw = player_info:user_display_name() or "Unknown"
            -- Fallback: also try character_name() if we don't have character name yet
            if character_name == "Unknown" then
                character_name = player_info:character_name() or "Unknown"
            end
        end
    end

    -- Extract platform and clean account name
    local platform, account_name = extract_platform(account_name_raw)

    local archetype_name = get_archetype_name(character_profile.archetype)

    -- Get character level
    local character_level = character_profile.current_level or "Unknown"

    -- Get export timestamp with timezone
    local export_date = os_lib.date("%Y-%m-%d %H:%M:%S")
    local timezone_offset = os_lib.date("%z") -- e.g., "-0500" or "+0100"

    -- Use echo with localization key and format args separately
    mod:info("Starting penance export for " .. character_name .. " (" .. archetype_name .. ")...")

    -- Get account-level data, XP table, and all character profiles from backend
    if Managers.backend and Managers.backend.interfaces and Managers.backend.interfaces.progression then
        local progression_promise = Managers.backend.interfaces.progression:get_entity_type_progression("character")
        local xp_promise = Managers.backend.interfaces.progression:get_xp_table("character")

        Promise.all(progression_promise, xp_promise):next(function(result)
            local characters_progression, xp_per_level_array = unpack(result)

            -- Build XP settings
            local xp_settings = {
                level_array = xp_per_level_array,
                total_xp = xp_per_level_array[#xp_per_level_array],
                max_level = #xp_per_level_array
            }

            -- Try to get profiles from already-loaded data
            local profile_lookup = {}
            local debug_log = {}

            -- Write debug log
            local function log_debug(msg)
                table.insert(debug_log, msg)
                mod:info(msg)
            end

            log_debug("=== Profile Loading Debug ===")
            log_debug(string.format("Timestamp: %s", os_lib.date("%Y-%m-%d %H:%M:%S")))

            -- Check for MainMenuView (character selection screen)
            if Managers.ui then
                log_debug("Managers.ui exists")
                local main_menu_active = Managers.ui:view_active("main_menu_view")
                log_debug(string.format("main_menu_view active: %s", tostring(main_menu_active)))

                if main_menu_active then
                    local view = Managers.ui:view_instance("main_menu_view")
                    if view then
                        log_debug("main_menu_view instance found")
                        if view._character_list_widgets then
                            log_debug(string.format("Found %d character widgets", #view._character_list_widgets))
                            for i, widget in ipairs(view._character_list_widgets) do
                                local content = widget.content
                                local prof = content.profile
                                if prof and prof.character_id then
                                    profile_lookup[prof.character_id] = prof
                                    log_debug(string.format("  [%d] %s (%s) - %s", i,
                                        prof.name or "?",
                                        prof.archetype and prof.archetype.name or "?",
                                        prof.character_id))
                                end
                            end
                        else
                            log_debug("No _character_list_widgets found")
                        end
                    else
                        log_debug("Could not get main_menu_view instance")
                    end
                end
            else
                log_debug("Managers.ui not available")
            end

            -- Use cached profiles if main menu isn't active
            if table.size(profile_lookup) == 0 and table.size(cached_character_profiles) > 0 then
                log_debug(string.format("Using %d cached character profiles", table.size(cached_character_profiles)))
                for char_id, prof in pairs(cached_character_profiles) do
                    profile_lookup[char_id] = prof
                    log_debug(string.format("  Cached: %s (%s) - %s",
                        prof.name or "?",
                        prof.archetype and prof.archetype.name or "?",
                        char_id))
                end
            end

            -- Also try backend.interfaces.profiles
            if Managers.backend and Managers.backend.interfaces and Managers.backend.interfaces.profiles then
                log_debug("backend.interfaces.profiles exists")
                local profiles_interface = Managers.backend.interfaces.profiles

                -- Try _profiles map
                if profiles_interface._profiles then
                    local count = 0
                    for char_id, prof in pairs(profiles_interface._profiles) do
                        profile_lookup[char_id] = prof
                        count = count + 1
                    end
                    log_debug(string.format("Loaded %d from _profiles", count))
                end

                -- Try _profiles_array
                if profiles_interface._profiles_array then
                    log_debug(string.format("_profiles_array: %d entries", #profiles_interface._profiles_array))
                    for _, prof in ipairs(profiles_interface._profiles_array) do
                        if prof.character_id then
                            profile_lookup[prof.character_id] = prof
                        end
                    end
                end
            else
                log_debug("backend.interfaces.profiles not available")
            end

            log_debug(string.format("Total profiles in lookup: %d", table.size(profile_lookup)))

            local num_characters = #characters_progression
            log_debug(string.format("Number of characters from progression: %d", num_characters))

            -- Notify if profiles aren't fully cached
            local profiles_loaded = table.size(profile_lookup)
            if profiles_loaded > 0 and profiles_loaded < num_characters then
                mod:notify(loc("notify_profiles_not_cached"))
                log_debug("Notified user: some character profiles not loaded")
            elseif profiles_loaded == 0 and num_characters > 1 then
                mod:notify(loc("notify_profiles_not_cached"))
                log_debug("Notified user: no character profiles loaded")
            end

            -- Write debug log to file
            local timestamp = os_lib.date("%Y%m%d_%H%M%S")
            local debug_filename = string.format("debug_export_%s.log", timestamp)
            local debug_filepath = string.format("%s/%s", mod_dir, debug_filename)
            log_debug(string.format("Writing debug log to: %s", debug_filepath))
            local debug_file = io_lib.open(debug_filepath, "w")
            if debug_file then
                for _, line in ipairs(debug_log) do
                    debug_file:write(line .. "\n")
                end
                debug_file:close()
                mod:info("Debug log written to " .. debug_filename)
            else
                mod:info("ERROR: Could not write debug log file")
            end
            local account_level = 0
            local account_true_level = 0
            local account_prestige = 0
            local all_characters = {}

            -- Find current character and calculate levels for all characters
            local character_id = character_profile.character_id
            local true_level, additional_level, prestige = nil, nil, nil

            for _, char_data in ipairs(characters_progression) do
                local char_level = char_data.currentLevel or 0
                local char_xp = char_data.currentXp or 0
                local char_true_level, char_additional, char_prestige = calculate_true_level(char_level, char_xp, xp_settings)
                char_true_level = char_true_level or char_level
                char_prestige = char_prestige or 0

                account_level = account_level + char_level
                account_true_level = account_true_level + char_true_level
                account_prestige = account_prestige + char_prestige

                -- Get character name and archetype from profile
                local char_profile = profile_lookup[char_data.id]
                local char_name = "Unknown"
                local char_archetype = "Unknown"

                if char_profile then
                    char_name = char_profile.name or char_name
                    if char_profile.archetype then
                        char_archetype = get_archetype_name(char_profile.archetype)
                    end
                else
                    -- Fallback: try to get from progression data if available
                    if char_data.characterName then
                        char_name = char_data.characterName
                    end
                    -- Show abbreviated character ID as last resort
                    if char_name == "Unknown" and char_data.id then
                        char_name = "Char-" .. string.sub(char_data.id, 1, 8)
                    end
                end

                -- Store character info
                table.insert(all_characters, {
                    id = char_data.id,
                    name = char_name,
                    archetype = char_archetype,
                    level = char_level,
                    true_level = char_true_level,
                    additional_level = char_additional or 0,
                    prestige = char_prestige or 0
                })

                -- Check if this is the current character
                if char_data.id == character_id then
                    true_level, additional_level, prestige = char_true_level, char_additional, char_prestige
                    -- Use the known current character info if profile lookup failed
                    if char_name == "Unknown" or string.match(char_name, "^Char%-") then
                        char_name = character_name
                        char_archetype = archetype_name
                        -- Update the stored info
                        all_characters[#all_characters].name = char_name
                        all_characters[#all_characters].archetype = char_archetype
                    end
                end
            end

            -- Continue with export after getting all data
            perform_export(player, character_profile, character_name, account_name, platform, account_id,
                archetype_name, character_level, export_date, timezone_offset, num_characters, account_level,
                true_level, additional_level, prestige, account_true_level, account_prestige, all_characters)
        end):catch(function(error)
            mod:info("Could not fetch account data, continuing without it...")
            -- Continue export without account data
            perform_export(player, character_profile, character_name, account_name, platform, account_id,
                archetype_name, character_level, export_date, timezone_offset, 0, 0, nil, nil, nil, 0, 0, {})
        end)

        return -- Exit early, export will continue in promise callback
    else
        -- Backend not available, continue without account data
        perform_export(player, character_profile, character_name, account_name, platform, account_id,
            archetype_name, character_level, export_date, timezone_offset, 0, 0, nil, nil, nil, 0, 0, {})
    end
end

-- Perform the actual export (separated to handle async account data)
perform_export = function(player, character_profile, character_name, account_name, platform, account_id, archetype_name, character_level, export_date, timezone_offset, num_characters, account_level, true_level, additional_level, prestige, account_true_level, account_prestige, all_characters)
    -- CSV header with metadata columns
    local csv_lines = {
        "Export_Account,Export_Platform,Export_Character,Export_Archetype,Export_Mod_Date,Achievement_ID,Category,Icon,Title,Description,Status,Progress,Goal,Progress_Percentage,Completion_Time,Score,Stats_Detail"
    }

    local total_penances = 0
    local completed_penances = 0

    -- Check if we're in the penance view (required for export)
    if not (Managers.ui and Managers.ui:view_active("penance_overview_view")) then
        mod:info("No achievement data available. Please open the Penance menu first!")
        mod:notify(loc("notify_no_data"))
        return
    end

    -- Get achievements data from the active view
    local achievements_data = nil
    local view = Managers.ui:view_instance("penance_overview_view")
    if view and view._achievements_by_category then
        achievements_data = view._achievements_by_category
    end

    if not achievements_data then
        mod:info("No achievement data available. Please open the Penance menu first!")
        mod:notify(loc("notify_no_data"))
        return
    end

    -- Collect all achievements by category
    for category_id, achievement_ids in pairs(achievements_data) do
        if achievement_ids and #achievement_ids > 0 then
            local category = AchievementCategories[category_id]

            for _, achievement_id in ipairs(achievement_ids) do
                local achievement = AchievementUIHelper.achievement_definition_by_id(achievement_id)
                local achievement_definition = Managers.achievements and Managers.achievements:achievement_definition(achievement_id)

                if achievement and achievement_definition then
                    total_penances = total_penances + 1

                    local is_completed, completion_time = false, nil
                    if Managers.achievements then
                        is_completed, completion_time = Managers.achievements:achievement_completed(player, achievement_id)
                    end

                    if is_completed then
                        completed_penances = completed_penances + 1
                    end

                    local progress, goal = 0, 1
                    local progress_percentage = 0

                    -- Get progress if achievement has progress tracking
                    local achievement_type = AchievementTypes[achievement_definition.type]
                    if achievement_type and achievement_type.get_progress then
                        local success, prog, gl = pcall(achievement_type.get_progress, achievement_definition, player)
                        if success then
                            progress, goal = prog or 0, gl or 1
                            if goal > 0 then
                                progress_percentage = math.floor((progress / goal) * 100)
                            end
                        end
                    end

                    -- Get icon texture path
                    local icon = ""
                    if achievement.icon then
                        icon = tostring(achievement.icon)
                    elseif achievement_definition.icon then
                        icon = tostring(achievement_definition.icon)
                    elseif achievement.icon_texture then
                        icon = tostring(achievement.icon_texture)
                    elseif achievement_definition.icon_texture then
                        icon = tostring(achievement_definition.icon_texture)
                    end

                    -- Collect detailed stats info
                    local stats_detail = ""
                    if achievement_definition.stats and Managers.stats then
                        local stat_parts = {}
                        local player_id = player.remote and player.stat_id or player:local_player_id()

                        for stat_name, stat_settings in pairs(achievement_definition.stats) do
                            local target = stat_settings.target or 0
                            local success, value = pcall(Managers.stats.read_user_stat, Managers.stats, player_id, stat_name)
                            if not success then
                                value = 0
                            end
                            value = math.min(value or 0, target)

                            local stat_display_name = StatDefinitions[stat_name] and StatDefinitions[stat_name].stat_name or stat_name
                            table.insert(stat_parts, string.format("%s: %d/%d", stat_display_name, value, target))
                        end
                        stats_detail = table.concat(stat_parts, "; ")
                    end

                    -- Build CSV row with metadata columns
                    local row = string.format("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%d,%d,%d%%,%s,%d,%s",
                        csv_escape(account_name),
                        csv_escape(platform),
                        csv_escape(character_name),
                        csv_escape(archetype_name),
                        csv_escape(export_date),
                        csv_escape(achievement_id),
                        csv_escape(category.display_name or "Unknown"),
                        csv_escape(icon),
                        csv_escape(AchievementUIHelper.localized_title(achievement_definition) or ""),
                        csv_escape(AchievementUIHelper.localized_description(achievement_definition) or ""),
                        csv_escape(is_completed and "Completed" or "In Progress"),
                        progress,
                        goal,
                        progress_percentage,
                        csv_escape(parse_completion_time(completion_time)),
                        achievement.score or 0,
                        csv_escape(stats_detail)
                    )

                    table.insert(csv_lines, row)
                end
            end
        end
    end

    -- Create directory if it doesn't exist
    os_lib.execute(string.format('mkdir "%s" 2>nul', mod_dir))

    -- Generate filename with account ID, date, and time
    local timestamp = os_lib.date("%Y%m%d_%H%M%S")
    local filename = string.format("%s_%s.csv", tostring(account_id), timestamp)
    local filepath = string.format("%s/%s", mod_dir, filename)

    -- Write CSV file
    local f, err = io_lib.open(filepath, "w")
    if f then
        -- Write metadata header as comments
        f:write(string.format("# Darktide Penance Export\n"))
        f:write(string.format("# Mod Version: %s\n", MOD_VERSION))
        f:write(string.format("# Account: %s\n", account_name))
        f:write(string.format("# Account ID: %s\n", tostring(account_id)))
        f:write(string.format("# Platform: %s\n", platform))
        if num_characters > 0 then
            f:write(string.format("# Number of Characters: %d\n", num_characters))
        end
        if account_level > 0 then
            f:write(string.format("# Account Level: %d\n", account_level))
        end
        if account_true_level and account_true_level > 0 then
            f:write(string.format("# Account True Level: %d\n", account_true_level))
        end
        if account_prestige and account_prestige > 0 then
            f:write(string.format("# Account Prestige: %d\n", account_prestige))
        end
        f:write(string.format("#\n"))

        -- List all characters
        if #all_characters > 0 then
            f:write(string.format("# All Characters:\n"))
            local has_unknowns = false
            for i, char in ipairs(all_characters) do
                local level_display = char.level
                if char.true_level > char.level then
                    level_display = string.format("%d (True: %d, Prestige: %d)", char.level, char.true_level, char.prestige)
                end
                f:write(string.format("#   %d. %s (%s) - Level %s\n", i, char.name, char.archetype, level_display))
                if string.match(char.name, "^Char%-") or char.name == "Unknown" then
                    has_unknowns = true
                end
            end
            if has_unknowns then
                f:write(string.format("#   Note: Visit main menu character selection to load all character names\n"))
            end
            f:write(string.format("#\n"))
        end

        -- Export character (the one whose penances are being exported)
        f:write(string.format("# Export Character: %s\n", character_name))
        f:write(string.format("# Export Archetype: %s\n", archetype_name))
        f:write(string.format("# Export Character Level: %s\n", tostring(character_level)))
        if true_level and true_level > character_level then
            f:write(string.format("# Export Character True Level: %d\n", true_level))
            if additional_level and additional_level > 0 then
                f:write(string.format("# Export Additional Levels: +%d\n", additional_level))
            end
            if prestige and prestige > 0 then
                f:write(string.format("# Export Character Prestige: %d\n", prestige))
            end
        end
        f:write(string.format("#\n"))
        f:write(string.format("# Export Date: %s\n", export_date))
        f:write(string.format("# Export Timezone: %s\n", timezone_offset))
        f:write(string.format("# Total Penances: %d\n", total_penances))
        f:write(string.format("# Completed Penances: %d\n", completed_penances))
        f:write(string.format("# Completion Rate: %.1f%%\n", total_penances > 0 and (completed_penances / total_penances * 100) or 0))
        f:write("\n")

        -- Write CSV data
        for _, line in ipairs(csv_lines) do
            f:write(line .. "\n")
        end

        f:close()
        mod:info("Penances exported to " .. filename .. "! Total: " .. total_penances .. " penances, Completed: " .. completed_penances)
        mod:notify(loc("notify_export_success") .. "\n{#size(11)}" .. filename .. "{#reset()}")
    else
        local error_msg = err or "unknown error"
        mod:info("Failed to export penances: " .. error_msg)
        mod:notify(loc("notify_export_failed") .. " " .. error_msg)
    end
end

-- Set up hooks to cache player data like the working mods do
mod.on_all_mods_loaded = function()
    -- Hook into the penance view to cache player and achievement data when available
    mod:hook_safe("PenanceOverviewView", "_build_achievements_cache", function(self)
        if self and self:_player() then
            cached_player = self:_player()
        end
        if self and self._achievements_by_category then
            cached_achievements_by_category = table.clone(self._achievements_by_category)
        end
    end)

    -- Hook into game state changes to maintain player reference
    mod:hook_safe("PenanceOverviewView", "on_enter", function(self)
        if self and self:_player() then
            cached_player = self:_player()
        end
        if self and self._achievements_by_category then
            cached_achievements_by_category = table.clone(self._achievements_by_category)
        end
    end)

    -- Hook into MainMenuView to cache character profiles when available
    mod:hook_safe("MainMenuView", "update", function(self)
        if self._character_list_widgets then
            for _, widget in ipairs(self._character_list_widgets) do
                local content = widget.content
                local prof = content.profile
                if prof and prof.character_id then
                    -- Cache this character's profile
                    cached_character_profiles[prof.character_id] = {
                        character_id = prof.character_id,
                        name = prof.name,
                        archetype = prof.archetype
                    }
                end
            end
        end
    end)

    mod:command("export_penances", "Export all penance data for current operative to CSV file", function()
        export_penances_csv()
    end)

    mod:command("debug_player", "Debug player and character info to find correct field names", function()
        debug_player_info()
    end)

    mod:echo(loc("msg_mod_loaded") .. " v" .. MOD_VERSION .. " " .. loc("msg_mod_loaded_suffix"))
end

-- Export function needs to be a mod method for keybind to work
mod.export_penances_csv = export_penances_csv
