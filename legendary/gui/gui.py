#!/usr/bin/env python3

# TODO: games' contextual menu, tooltip show all info progress bar

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '../..')

import webbrowser
import time
from multiprocessing import freeze_support, Queue as MPQueue
import os
import shlex

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

import legendary.core
import legendary.cli
from legendary.gui.vars import args_obj
core = legendary.core.LegendaryCore()
cli = legendary.cli.LegendaryCLI()

def update_gui(main_window, dlm):
               # perc,
               # processed_chunks, num_chunk_tasks,
               # rt_hours, rt_minutes, rt_seconds,
               # hours, minutes, seconds,
               # total_dl, total_write, total_used,
               # dl_speed, dl_unc_speed, w_speed, r_speed,
    print(f"update_gui_{main_window.progress_bar}")
    #print(f"{dlm}")
    #print(f"dhexid:{hex(id(dlm.perc))}")
    time.sleep(0.100)
    if not main_window.bar_queue.empty():
        perc = main_window.bar_queue.get()
        processed_chunks = main_window.bar_queue.get()
        num_chunk_tasks = main_window.bar_queue.get()
        rt_hours = main_window.bar_queue.get()
        rt_minutes = main_window.bar_queue.get()
        rt_seconds = main_window.bar_queue.get()
        hours = main_window.bar_queue.get()
        minutes = main_window.bar_queue.get()
        seconds = main_window.bar_queue.get()
        total_dl = main_window.bar_queue.get()
        total_write = main_window.bar_queue.get()
        total_used = main_window.bar_queue.get()
        dl_speed = main_window.bar_queue.get()
        dl_unc_speed = main_window.bar_queue.get()
        w_speed = main_window.bar_queue.get()
        r_speed = main_window.bar_queue.get()
        main_window.progress_bar.set_fraction(perc)
        main_window.progress_bar.set_text(f"{dl_speed / 1024 / 1024:.02f} MiB/s - {(perc*100):.02f}% - ETA: {hours:02d}:{minutes:02d}:{seconds:02d}")
        ##a## main_window.progress_bar.set_text(f"{parent.values_dlm[0] / 1024 / 1024:.02f} MiB/s - {(parent.values_dlm[0]*100):.02f}% - ETA: {parent.values_dlm[6]:02d}:{parent.values_dlm[7]:02d}:{parent.values_dlm[8]:02d}")
        main_window.progress_bar.set_tooltip_text("tooltip") # show all infos that are also in update_cli()
    print(main_window.progress_bar.get_text())
    if not dlm.is_alive():
        print("Completing...")
        main_window.progress_bar.set_text("Completing...")
        main_window.progress_bar.set_tooltip_text("Finishing...")
        post_dlm(main_window)
        main_window.progress_bar.set_text("Nothing in download")
        main_window.progress_bar.set_tooltip_text("Nothing in download")
        main_window.progress_bar.set_fraction(0)
        main_window.scroll.destroy()
        main_window.list_games()
        print("finished post_dlm and update_gui")
        return False
    return True # since this is a timeout function

def log_gtk(msg):
    dialog = Gtk.Dialog(title="Legendary Log")
    dialog.log = Gtk.Label(label=msg)
    dialog.log.set_selectable(True)
    box = dialog.get_content_area()
    box.add(dialog.log)
    return dialog
    #dialog.show_all()

def is_installed(app_name):
    if core.get_installed_game(app_name) == None:
        return "No"
    else:
        return "Yes"

def installed_size(app_name):
    g = core.get_installed_game(app_name)
    if g == None:
        return ""
    else:
        return f"{g.install_size / (1024*1024*1024):.02f} GiB"

def update_avail(app_name):
    print_version = False # temporary, this will be in the config
    g = core.get_installed_game(app_name)
    if g != None:
        try:
            version = core.get_asset(app_name).build_version
        except ValueError:
            log_gtk(f'Metadata for "{game.app_name}" is missing, the game may have been removed from '
                           f'your account or not be in legendary\'s database yet, try rerunning the command '
                           f'with "--check-updates".').show_all()
        if version != g.version:
            if print_version: # for future config
                return f"Yes (Old: {g.version}; New: {version})"
            else:
                return f"Yes"
        else:
            return "No"
    else:
        return ""

def install_gtk(app_name, app_title, parent):
    install_dialog = Gtk.MessageDialog( parent=parent,
                                        destroy_with_parent=True,
                                        message_type=Gtk.MessageType.QUESTION,
                                        buttons=Gtk.ButtonsType.OK_CANCEL,
                                        text=f"Install {app_title} (Leave entries blank to use the default)"
                                      )
    install_dialog.set_title(f"Install {app_title}")
    install_dialog.set_default_size(400, 0)
    vbox = install_dialog.get_content_area()

    # advanced options declaration
    show_advanced = False
    show_advanced_check_button = Gtk.CheckButton(label="Show advanced options")
    show_advanced_check_button.set_tooltip_text("Show more options")
    vbox.add(show_advanced_check_button)
    advanced_options = Gtk.VBox(spacing=5)

    # --base-path <path>
    base_path_box = Gtk.HBox()
    base_path_label = Gtk.Label(label="Base Path")
    base_path_label.set_tooltip_text("Path for game installations (defaults to ~/legendary)")
    base_path_entry = Gtk.Entry()
    base_path_file_chooser_button = Gtk.Button(label="Browse")
    def base_path_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the base path",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.SELECT_FOLDER,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        base_path_file_response = fc.run()
        if base_path_file_response == Gtk.ResponseType.OK:
            base_path_entry.set_text(fc.get_filename())
            print("Folder selected for base path:"+fc.get_filename())
        fc.destroy()
    base_path_file_chooser_button.connect("clicked",base_path_choose_f)
    base_path_box.pack_end(base_path_file_chooser_button, False, False, 5)
    base_path_box.pack_start(base_path_label, False, False, 10)
    base_path_box.pack_start(base_path_entry, True, True, 0)
    vbox.add(base_path_box)

    # --game-folder <path>
    game_folder_box = Gtk.HBox()
    game_folder_label = Gtk.Label(label="Game Folder")
    game_folder_label.set_tooltip_text("Folder for game installation (defaults to folder specified in metadata")
    game_folder_entry = Gtk.Entry()
    game_folder_file_chooser_button = Gtk.Button(label="Browse")
    def game_folder_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the game folder",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.SELECT_FOLDER,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        game_folder_file_response = fc.run()
        if game_folder_file_response == Gtk.ResponseType.OK:
            game_folder_entry.set_text(fc.get_filename())
            print("Folder selected for game folder:"+fc.get_filename())
        fc.destroy()
    game_folder_file_chooser_button.connect("clicked",game_folder_choose_f)
    game_folder_box.pack_end(game_folder_file_chooser_button, False, False, 5)
    game_folder_box.pack_start(game_folder_label, False, False, 10)
    game_folder_box.pack_start(game_folder_entry, True, True, 0)
    vbox.add(game_folder_box)

    # --max-shared-memory <size> (in MiB)
    max_shm_box = Gtk.HBox()
    max_shm_label = Gtk.Label(label="Max Shared Memory")
    max_shm_label.set_tooltip_text("Maximum amount of shared memory to use (in MiB), default: 1 GiB")
    max_shm_entry = Gtk.Entry()
    max_shm_box.pack_start(max_shm_label, False, False, 10)
    max_shm_box.pack_start(max_shm_entry, True, True, 0)
    advanced_options.add(max_shm_box)

    # --max-workers <num>
    max_workers_box = Gtk.HBox()
    max_workers_label = Gtk.Label(label="Max Workers")
    max_workers_label.set_tooltip_text("Maximum amount of download workers, default: min(2 * CPUs, 16)")
    max_workers_entry = Gtk.Entry()
    max_workers_box.pack_start(max_workers_label, False, False, 10)
    max_workers_box.pack_start(max_workers_entry, True, True, 0)
    advanced_options.add(max_workers_box)

    # --manifest <uri>
    override_manifest_box = Gtk.HBox()
    override_manifest_label = Gtk.Label(label="Manifest")
    override_manifest_label.set_tooltip_text("Manifest URL or path to use instead of the CDN one (e.g. for downgrading)")
    override_manifest_entry = Gtk.Entry()
    override_manifest_file_chooser_button = Gtk.Button(label="Browse")
    def override_manifest_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the manifest",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.OPEN,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        override_manifest_file_response = fc.run()
        if override_manifest_file_response == Gtk.ResponseType.OK:
            override_manifest_entry.set_text(fc.get_filename())
            print("Folder selected for manifest:"+fc.get_filename())
        fc.destroy()
    override_manifest_file_chooser_button.connect("clicked",override_manifest_choose_f)
    override_manifest_box.pack_end(override_manifest_file_chooser_button, False, False, 5)
    override_manifest_box.pack_start(override_manifest_label, False, False, 10)
    override_manifest_box.pack_start(override_manifest_entry, True, True, 0)
    advanced_options.add(override_manifest_box)

    # --old-manifest <uri>
    override_old_manifest_box = Gtk.HBox()
    override_old_manifest_label = Gtk.Label(label="Old Manifest")
    override_old_manifest_label.set_tooltip_text("Manifest URL or path to use as the old one (e.g. for testing patching)")
    override_old_manifest_entry = Gtk.Entry()
    override_old_manifest_file_chooser_button = Gtk.Button(label="Browse")
    def override_old_manifest_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the old manifest",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.OPEN,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        override_old_manifest_file_response = fc.run()
        if override_old_manifest_file_response == Gtk.ResponseType.OK:
            override_old_manifest_entry.set_text(fc.get_filename())
            print("Folder selected for old manifest:"+fc.get_filename())
        fc.destroy()
    override_old_manifest_file_chooser_button.connect("clicked",override_old_manifest_choose_f)
    override_old_manifest_box.pack_end(override_old_manifest_file_chooser_button, False, False, 5)
    override_old_manifest_box.pack_start(override_old_manifest_label, False, False, 10)
    override_old_manifest_box.pack_start(override_old_manifest_entry, True, True, 0)
    advanced_options.add(override_old_manifest_box)

    # --delta-manifest <uri>
    override_delta_manifest_box = Gtk.HBox()
    override_delta_manifest_label = Gtk.Label(label="Delta Manifest")
    override_delta_manifest_label.set_tooltip_text("Manifest URL or path to use as the delta one (e.g. for testing)")
    override_delta_manifest_entry = Gtk.Entry()
    override_delta_manifest_file_chooser_button = Gtk.Button(label="Browse")
    def override_delta_manifest_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the delta manifest",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.OPEN,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        override_delta_manifest_file_response = fc.run()
        if override_delta_manifest_file_response == Gtk.ResponseType.OK:
            override_delta_manifest_entry.set_text(fc.get_filename())
            print("Folder selected for delta manifest:"+fc.get_filename())
        fc.destroy()
    override_delta_manifest_file_chooser_button.connect("clicked",override_delta_manifest_choose_f)
    override_delta_manifest_box.pack_end(override_delta_manifest_file_chooser_button, False, False, 5)
    override_delta_manifest_box.pack_start(override_delta_manifest_label, False, False, 10)
    override_delta_manifest_box.pack_start(override_delta_manifest_entry, True, True, 0)
    advanced_options.add(override_delta_manifest_box)

    # --base-url <url>
    override_base_url_box = Gtk.HBox()
    override_base_url_label = Gtk.Label(label="Base Url")
    override_base_url_label.set_tooltip_text("Base URL to download from (e.g. to test or switch to a different CDNs)")
    override_base_url_entry = Gtk.Entry()
    override_base_url_box.pack_start(override_base_url_label, False, False, 10)
    override_base_url_box.pack_start(override_base_url_entry, True, True, 0)
    advanced_options.add(override_base_url_box)

    # --force
    force = False
    force_check_button = Gtk.CheckButton(label="Force install")
    force_check_button.set_tooltip_text("Download all files / ignore existing (overwrite)")
    #def force_button_toggled(button, name):
    #    if button.get_active():
    #        force = True
    #    else:
    #        force = False
    #    print(name, "is now", force)
    #force_check_button.connect("toggled", force_button_toggled, "force")
    advanced_options.add(force_check_button)

    # --disable-patching
    disable_patching = False
    disable_patching_check_button = Gtk.CheckButton(label="Disable patching")
    disable_patching_check_button.set_tooltip_text("Do not attempt to patch existing installation (download entire changed files)")
    #def disable_patching_button_toggled(button, name):
    #    if button.get_active():
    #        disable_patching = True
    #    else:
    #        disable_patching = False
    #    print(name, "is now", disable_patching)
    #disable_patching_check_button.connect("toggled", disable_patching_button_toggled, "disable_patching")
    advanced_options.add(disable_patching_check_button)

    # --download-only, --no-install
    download_only = False
    download_only_check_button = Gtk.CheckButton(label="Download only")
    download_only_check_button.set_tooltip_text("Do not intall app and do not run prerequisite installers after download")
    #def download_only_button_toggled(button, name):
    #    if button.get_active():
    #        download_only = True
    #    else:
    #        download_only = False
    #    print(name, "is now", download_only)
    #download_only_check_button.connect("toggled", download_only_button_toggled, "download_only")
    advanced_options.add(download_only_check_button)

    # --update-only
    update_only = False
    update_only_check_button = Gtk.CheckButton(label="Update only")
    update_only_check_button.set_tooltip_text("Only update, do not do anything if specified app is not installed")
    #def update_only_button_toggled(button, name):
    #    if button.get_active():
    #        update_only = True
    #    else:
    #        update_only = False
    #    print(name, "is now", update_only)
    #update_only_check_button.connect("toggled", update_only_button_toggled, "update_only")
    advanced_options.add(update_only_check_button)

    # --dlm-debug
    dlm_debug = False
    dlm_debug_check_button = Gtk.CheckButton(label="Downloader debug messages")
    dlm_debug_check_button.set_tooltip_text("Set download manager and worker processes' loglevel to debug")
    #def dlm_debug_button_toggled(button, name):
    #    if button.get_active():
    #        dlm_debug = True
    #    else:
    #        dlm_debug = False
    #    print(name, "is now", dlm_debug)
    #dlm_debug_check_button.connect("toggled", dlm_debug_button_toggled, "dlm_debug")
    advanced_options.add(dlm_debug_check_button)
    
	# --platform <Platform> # use drop-down menu
    platform_override_box = Gtk.HBox()
    platform_override_label = Gtk.Label(label="Platform")
    platform_override_label.set_tooltip_text("Platform override for download (also sets 'Download Only')")
    platform_override_entry = Gtk.Entry()
    platform_override_box.pack_start(platform_override_label, False, False, 10)
    platform_override_box.pack_start(platform_override_entry, True, True, 0)
    advanced_options.add(platform_override_box)
    
	# --prefix <prefix>
    file_prefix_filter_box = Gtk.HBox()
    file_prefix_filter_label = Gtk.Label(label="File prefix filter")
    file_prefix_filter_label.set_tooltip_text("Only fetch files whose path starts with <prefix> (case insensitive)")
    file_prefix_filter_entry = Gtk.Entry()
    file_prefix_filter_entry.set_placeholder_text("<prefix>")
    file_prefix_filter_box.pack_start(file_prefix_filter_label, False, False, 10)
    file_prefix_filter_box.pack_start(file_prefix_filter_entry, True, True, 0)
    advanced_options.add(file_prefix_filter_box)
    
	# --exclude <prefix>
    file_exclude_filter_box = Gtk.HBox()
    file_exclude_filter_label = Gtk.Label(label="File exclude filter")
    file_exclude_filter_label.set_tooltip_text("Exclude files starting with <prefix> (case insensitive)")
    file_exclude_filter_entry = Gtk.Entry()
    file_exclude_filter_entry.set_placeholder_text("<prefix>")
    file_exclude_filter_box.pack_start(file_exclude_filter_label, False, False, 10)
    file_exclude_filter_box.pack_start(file_exclude_filter_entry, True, True, 0)
    advanced_options.add(file_exclude_filter_box)
    
	# --install-tag <tag>
    file_install_tag_box = Gtk.HBox()
    file_install_tag_label = Gtk.Label(label="Install tag")
    file_install_tag_label.set_tooltip_text("Only download files with the specified install tag")
    file_install_tag_entry = Gtk.Entry()
    file_install_tag_box.pack_start(file_install_tag_label, False, False, 10)
    file_install_tag_box.pack_start(file_install_tag_entry, True, True, 0)
    advanced_options.add(file_install_tag_box)
    
	# --enable-reordering
    enable_reordering = False
    enable_reordering_check_button = Gtk.CheckButton(label="Enable reordering optimization")
    enable_reordering_check_button.set_tooltip_text("Enable reordering optimization to reduce RAM requirements during download (may have adverse results for some titles)")
    #def enable_reordering_button_toggled(button, name):
    #    if button.get_active():
    #        enable_reordering = True
    #    else:
    #        enable_reordering = False
    #    print(name, "is now", enable_reordering)
    #enable_reordering_check_button.connect("toggled", enable_reordering_button_toggled, "enable_reordering")
    advanced_options.add(enable_reordering_check_button)
    
	# --dl-timeout <sec> # use number thingy with - 00 +
    dl_timeout_box = Gtk.HBox()
    dl_timeout_label = Gtk.Label(label="Downloader timeout")
    dl_timeout_label.set_tooltip_text("Connection timeout for downloader (default: 10 seconds)")
    dl_timeout_entry = Gtk.Entry()
    dl_timeout_box.pack_start(dl_timeout_label, False, False, 10)
    dl_timeout_box.pack_start(dl_timeout_entry, True, True, 0)
    advanced_options.add(dl_timeout_box)
    
	# --save-path <path>
    save_path_box = Gtk.HBox()
    save_path_label = Gtk.Label(label="Save path")
    save_path_label.set_tooltip_text("Set save game path to be used for sync-saves")
    save_path_entry = Gtk.Entry()
    save_path_file_chooser_button = Gtk.Button(label="Browse")
    def save_path_choose_f(self):
        # fc = file chooser
        fc = Gtk.FileChooserDialog(title="Please choose the save path",
                                                parent=install_dialog,
                                                action=Gtk.FileChooserAction.SELECT_FOLDER,
                                                destroy_with_parent=True
        )
        fc.add_buttons(Gtk.STOCK_CANCEL,
                                    Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,
                                    Gtk.ResponseType.OK
        )
        fc.set_default_size(600, 300)
        save_path_file_response = fc.run()
        if save_path_file_response == Gtk.ResponseType.OK:
            save_path_entry.set_text(fc.get_filename())
            print("Folder selected for save path:"+fc.get_filename())
        fc.destroy()
    save_path_file_chooser_button.connect("clicked",save_path_choose_f)
    save_path_box.pack_end(save_path_file_chooser_button, False, False, 5)
    save_path_box.pack_start(save_path_label, False, False, 10)
    save_path_box.pack_start(save_path_entry, True, True, 0)
    advanced_options.add(save_path_box)
    
	# --repair
    repair = False
    repair_check_button = Gtk.CheckButton(label="Repair")
    repair_check_button.set_tooltip_text("Repair installed game by checking and redownloading corrupted/missing files")
    #def repair_button_toggled(button, name):
    #    if button.get_active():
    #        repair = True
    #    else:
    #        repair = False
    #    print(name, "is now", repair)
    #repair_check_button.connect("toggled", repair_button_toggled, "repair")
    advanced_options.add(repair_check_button)
    
	# --repair-and-update
    repair_and_update = False # or repair_use_latest
    repair_and_update_check_button = Gtk.CheckButton(label="Repair and Update")
    repair_and_update_check_button.set_tooltip_text("Update game to the latest version when repairing")
    #def repair_and_update_button_toggled(button, name):
    #    if button.get_active():
    #        repair_and_update = True
    #    else:
    #        repair_and_update = False
    #    print(name, "is now", repair_and_update)
    #repair_and_update_check_button.connect("toggled", repair_and_update_button_toggled, "repair_and_update")
    advanced_options.add(repair_and_update_check_button)
    
	# --ignore-free-space
    ignore_space_req = False
    ignore_space_req_check_button = Gtk.CheckButton(label="Ignore space requirements")
    ignore_space_req_check_button.set_tooltip_text("Do not abort if not enough free space is available")
    #def ignore_space_req_button_toggled(button, name):
    #    if button.get_active():
    #        ignore_space_req = True
    #    else:
    #        ignore_space_req = False
    #    print(name, "is now", ignore_space_req)
    #ignore_space_req_check_button.connect("toggled", ignore_space_req_button_toggled, "ignore_space_req")
    advanced_options.add(ignore_space_req_check_button)
    
	# --disable-delta-manifests
    disable_delta_manifest = False
    disable_delta_manifest_check_button = Gtk.CheckButton(label="Disable delta manifests")
    disable_delta_manifest_check_button.set_tooltip_text("Do not use delta manifests when updating (may increase download size)")
    #def override_delta_manifest_button_toggled(button, name):
    #    if button.get_active():
    #        override_delta_manifest = True
    #    else:
    #        override_delta_manifest = False
    #    print(name, "is now", override_delta_manifest)
    #override_delta_manifest_check_button.connect("toggled", override_delta_manifest_button_toggled, "override_delta_manifest")
    advanced_options.add(disable_delta_manifest_check_button)
    
	# --reset-sdl
    reset_sdl = False
    reset_sdl_check_button = Gtk.CheckButton(label="Reset selective downloading choices")
    reset_sdl_check_button.set_tooltip_text("Reset selective downloading choices (requires repair to download new components)")
    #def reset_sdl_button_toggled(button, name):
    #    if button.get_active():
    #        reset_sdl = True
    #    else:
    #        reset_sdl = False
    #    print(name, "is now", reset_sdl)
    #reset_sdl_check_button.connect("toggled", reset_sdl_button_toggled, "reset_sdl")
    advanced_options.add(reset_sdl_check_button)


    vbox.add(advanced_options)
    # advanced_options function
    def show_advanced_button_toggled(button, name):
        if button.get_active():
            show_advanced = True
            advanced_options.set_no_show_all(False)
            install_dialog.show_all()
        else:
            show_advanced = False
            advanced_options.hide()
        install_dialog.resize(400,5)
        print(name, "is now", show_advanced)
    show_advanced_check_button.connect("toggled", show_advanced_button_toggled, "show_advanced")

    advanced_options.set_no_show_all(True)
    install_dialog.show_all()
    install_dialog_response = install_dialog.run()

    parent.args = args_obj()
    # entries
    parent.args.base_path = base_path_entry.get_text()
    parent.args.game_folder = game_folder_entry.get_text()
    parent.args.shared_memory = max_shm_entry.get_text()
    parent.args.max_workers = max_workers_entry.get_text()
    parent.args.override_manifest = override_manifest_entry.get_text()
    parent.args.override_old_manifest = override_old_manifest_entry.get_text()
    parent.args.override_delta_manifest = override_delta_manifest_entry.get_text()
    parent.args.override_base_url = override_base_url_entry.get_text()
    parent.args.platform_override = platform_override_entry.get_text()
    parent.args.file_prefix = file_prefix_filter_entry.get_text()
    parent.args.file_exclude_prefix = file_exclude_filter_entry.get_text()
    parent.args.install_tag = file_install_tag_entry.get_text()
    parent.args.dl_timeout = dl_timeout_entry.get_text()
    parent.args.save_path = save_path_entry.get_text()
    # check boxes
    parent.args.force = force_check_button.get_active()
    parent.args.disable_patching = disable_patching_check_button.get_active()
    parent.args.no_install = download_only_check_button.get_active()
    parent.args.update_only = update_only_check_button.get_active()
    parent.args.dlm_debug = dlm_debug_check_button.get_active()
    parent.args.order_opt = enable_reordering_check_button.get_active()
    parent.args.repair_mode = repair_check_button.get_active()
    parent.args.repair_and_update = repair_and_update_check_button.get_active()
    parent.args.ignore_space = ignore_space_req_check_button.get_active()
    parent.args.disable_delta = disable_delta_manifest_check_button.get_active()
    parent.args.reset_sdl = reset_sdl_check_button.get_active()

    if install_dialog_response != Gtk.ResponseType.OK:
        install_dialog.destroy()
        return 1

    print(  f"base_path:\t\t {parent.args.base_path}",
            f"game_folder:\t\t {parent.args.game_folder}",
            f"max_shm:\t\t {parent.args.shared_memory}",
            f"max_workers:\t\t {parent.args.max_workers}",
            f"override_manifest:\t {parent.args.override_manifest}",
            f"override_old_manifest:\t {parent.args.override_old_manifest}",
            f"override_delta_manifest: {parent.args.override_delta_manifest}",
            f"override_base_url:\t {parent.args.override_base_url}",
            f"platform_override:\t {parent.args.platform_override}",
            f"file_prefix_filter:\t {parent.args.file_prefix}",
            f"file_exclude_filter:\t {parent.args.file_exclude_prefix}",
            f"file_install_tag:\t {parent.args.install_tag}",
            f"dl_timeout:\t\t {parent.args.dl_timeout}",
            f"save_path:\t\t {parent.args.save_path}",
            f"force:\t\t\t {parent.args.force}",
            f"disable_patching:\t {parent.args.disable_patching}",
            f"download_only:\t\t {parent.args.no_install}",
            f"update_only:\t\t {parent.args.update_only}",
            f"dlm_debug:\t\t {parent.args.dlm_debug}",
            f"enable_reordering:\t {parent.args.order_opt}",
            f"repair:\t\t\t {parent.args.repair_mode}",
            f"repair_and_update:\t {parent.args.repair_and_update}",
            f"ignore_space_req:\t {parent.args.ignore_space}",
            f"reset_sdl:\t\t {parent.args.reset_sdl}",
    sep='\n'
    )

    install_dialog.hide()
    if core.is_installed(app_name):
        parent.igame = core.get_installed_game(app_name)
        if parent.igame.needs_verification:
            repair_mode = True
    repair_file = None
    if parent.args.repair_mode:
        parent.args.no_install = parent.args.repair_and_update is False
        repair_file = os.path.join(core.lgd.get_tmp_path(), f'{app_name}.repair')

    if not core.login():
        log_gtk('Login failed! Cannot continue with download process.').show_all()
        print('Login failed! Cannot continue with download process.')
        return 1

    if parent.args.file_prefix or parent.args.file_exclude_prefix or parent.args.install_tag:
        parent.args.no_install = True

    if parent.args.update_only:
        if not core.is_installed(app_name):
            log_gtk(f'Update requested for "{app_name}", but app not installed!').show_all()
            print(f'Update requested for "{app_name}", but app not installed!')
            return 1

    if parent.args.platform_override:
        parent.args.no_install = True

    parent.game = core.get_game(app_name, update_meta=True)

    if not parent.game:
        log_gtk(f'Could not find "{app_name}" in list of available games,'
                     f'did you type the name correctly?').show_all()
        print(f'Could not find "{app_name}" in list of available games,'
                     f'did you type the name correctly?')
        return 1

    if parent.game.is_dlc:
        #log_gtk('Install candidate is DLC').show_all()
        print('Install candidate is DLC')
        app_name = parent.game.metadata['mainGameItem']['releaseInfo'][0]['appId']
        base_game = core.get_game(app_name)
        # check if base_game is actually installed
        if not core.is_installed(app_name):
            # download mode doesn't care about whether or not something's installed
            if not parent.args.no_install:
                log_gtk(f'Base parent.game "{app_name}" is not installed!').show_all()
                print(f'Base parent.game "{app_name}" is not installed!')
                return 1
    else:
        base_game = None

    #if parent.args.repair_mode:
    #    if not core.is_installed(parent.game.app_name):
    #        log_gtk(f'Game "{parent.game.app_title}" ({parent.game.app_name}) is not installed!').show_all()
    #        exit(0)

    #    if not os.path.exists(repair_file):
    #        log_gtk('Game has not been verified yet.').show_all()
    #        if not parent.args.yes:
    #            if not get_boolean_choice(f'Verify "{parent.game.app_name}" now ("no" will abort repair)?'):
    #                print('Aborting...')
    #                exit(0)

    #        self.verify_game(parent.args, print_command=False)
    #    else:
    #        log_gtk(f'Using existing repair file: {repair_file}').show_all()

    # Workaround for Cyberpunk 2077 preload
    #if not parent.args.install_tag and not parent.game.is_dlc and ((sdl_name := get_sdl_appname(parent.game.app_name)) is not None):
    #    config_tags = core.lgd.config.get(parent.game.app_name, 'install_tags', fallback=None)
    #    if not core.is_installed(parent.game.app_name) or config_tags is None or parent.args.reset_sdl:
    #        parent.args.install_tag = sdl_prompt(sdl_name, parent.game.app_title)
    #        if parent.game.app_name not in core.lgd.config:
    #            core.lgd.config[parent.game.app_name] = dict()
    #        core.lgd.config.set(parent.game.app_name, 'install_tags', ','.join(parent.args.install_tag))
    #    else:
    #        parent.args.install_tag = config_tags.split(',')

    print('Preparing download...')
    # todo use status queue to print progress from CLI
    # This has become a little ridiculous hasn't it?
    dlm, analysis, parent.igame = core.prepare_download(game=parent.game, base_game=base_game, base_path=parent.args.base_path,
                                                      force=parent.args.force, max_shm=parent.args.shared_memory,
                                                      max_workers=parent.args.max_workers, game_folder=parent.args.game_folder,
                                                      disable_patching=parent.args.disable_patching,
                                                      override_manifest=parent.args.override_manifest,
                                                      override_old_manifest=parent.args.override_old_manifest,
                                                      override_base_url=parent.args.override_base_url,
                                                      platform_override=parent.args.platform_override,
                                                      file_prefix_filter=parent.args.file_prefix,
                                                      file_exclude_filter=parent.args.file_exclude_prefix,
                                                      file_install_tag=parent.args.install_tag,
                                                      dl_optimizations=parent.args.order_opt,
                                                      dl_timeout=parent.args.dl_timeout,
                                                      repair=parent.args.repair_mode,
                                                      repair_use_latest=parent.args.repair_and_update,
                                                      disable_delta=parent.args.disable_delta,
                                                      override_delta_manifest=parent.args.override_delta_manifest,
                                                      main_window=parent)

    # parent.game is either up to date or hasn't changed, so we have nothing to do
    if not analysis.dl_size:
        old_igame = core.get_installed_game(parent.game.app_name)
        log_gtk(f'Download size is 0, {app_title} is either already up to date or has not changed.').show_all()
        if old_igame and parent.args.repair_mode and os.path.exists(repair_file):
            if old_igame.needs_verification:
                old_igame.needs_verification = False
                core.install_game(old_igame)

            #log_gtk('Removing repair file.').show_all()
            l=log_gtk('Removing repair file.').show_all()
            os.remove(repair_file)
            l.destroy()

        # check if install tags have changed, if they did; try deleting files that are no longer required.
        if old_igame and old_igame.install_tags != parent.igame.install_tags:
            old_igame.install_tags = parent.igame.install_tags
            #log_gtk('Deleting now untagged files.').show_all()
            l=log_gtk('Deleting now untagged files.').show_all()
            core.uninstall_tag(old_igame)
            core.install_game(old_igame)
            l.destroy()

        return 0

    print(f'Install size: {analysis.install_size / 1024 / 1024:.02f} MiB')
    compression = (1 - (analysis.dl_size / analysis.uncompressed_dl_size)) * 100
    print(f'Download size: {analysis.dl_size / 1024 / 1024:.02f} MiB '
                f'(Compression savings: {compression:.01f}%)')
    print(f'Reusable size: {analysis.reuse_size / 1024 / 1024:.02f} MiB (chunks) / '
                f'{analysis.unchanged / 1024 / 1024:.02f} MiB (unchanged / skipped)')

    res = core.check_installation_conditions(analysis=analysis, install=parent.igame, game=parent.game,
                                                  updating=core.is_installed(app_name),
                                                  ignore_space_req=parent.args.ignore_space)

    if res.warnings or res.failures:
        #log_gtk('Installation requirements check returned the following results:').show_all()
        print('Installation requirements check returned the following results:')

    if res.warnings:
        for warn in sorted(res.warnings):
            #log_gtk(warn).show_all()
            print(warn)

    if res.failures:
        for msg in sorted(res.failures):
            #log_gtk(msg).show_all()
            print(msg)
        log_gtk('Installation cannot proceed, exiting.').show_all()
        return 1

    print('Downloads are resumable, you can interrupt the download with '
                'CTRL-C and resume it using the same command later on.')

    do_install_dialog = Gtk.MessageDialog(
                                        parent=parent,
                                        destroy_with_parent=True,
                                        message_type=Gtk.MessageType.QUESTION,
                                        buttons=Gtk.ButtonsType.OK_CANCEL,
                                        text=f'Do you wish to install "{parent.igame.title}"?'
                                      )
    do_install_dialog.set_title(f"Install {app_title}")
    do_install_dialog.set_default_size(400, 0)
    box_stats = do_install_dialog.get_content_area()

    box_stats.label = Gtk.Label(
        label=f'Install size: {analysis.install_size / 1024 / 1024:.02f} MiB ({analysis.install_size / 1024 / 1024 / 1024:.03f} GiB)\n'
              f'Download size: {analysis.dl_size / 1024 / 1024:.02f} MiB ({analysis.dl_size / 1024 / 1024 / 1024:.03f} GiB) (Compression savings: {compression:.01f}%)\n'
              f'Reusable size: {analysis.reuse_size / 1024 / 1024:.02f} MiB (chunks) / {analysis.unchanged / 1024 / 1024:.02f} MiB (unchanged / skipped)'
            )
    box_stats.label.set_margin_start(10)
    box_stats.label.set_margin_end(10)
    box_stats.add(box_stats.label)

    #box_stats.label = Gtk.Label(label=f'Install size: {analysis.install_size / 1024 / 1024:.02f} MiB')
    #box_stats.add(box_stats.label)
    #box_stats.label = Gtk.Label(label=f'Download size: {analysis.dl_size / 1024 / 1024:.02f} MiB (Compression savings: {compression:.01f}%)')
    #box_stats.add(box_stats.label)
    #box_stats.label = Gtk.Label(label=f'Reusable size: {analysis.reuse_size / 1024 / 1024:.02f} MiB (chunks) / {analysis.unchanged / 1024 / 1024:.02f} MiB (unchanged / skipped)')
    #box_stats.add(box_stats.label)
    do_install_dialog.show_all()
    do_install_dialog_response = do_install_dialog.run()
    if do_install_dialog_response != Gtk.ResponseType.OK:
        do_install_dialog.destroy()
        return 1
    do_install_dialog.hide()
    


    parent.start_t = time.time()
#    GLib.idle_add(dlm_start, parent.args, dlm, start_t)
#
#def dlm_start(parent.args, dlm, start_t):


    try:
        # set up logging stuff (should be moved somewhere else later)
        dlm.logging_queue = cli.logging_queue
        dlm.proc_debug = parent.args.dlm_debug

        #print("parent:",parent)
    #    dlm.perc = 0
    #    dlm.dl_speed = 0
    #    dlm.hours = 0
    #    dlm.minutes = 0
    #    dlm.seconds = 0
    #bar.set_text(f"{dlm.dl_speed / 1024 / 1024:.02f} MiB/s - {(dlm.perc*100):.02f}% - ETA: {dlm.hours:02d}:{dlm.minutes:02d}:{dlm.seconds:02d}")
        dlm.start()
        #time.sleep(4)
        #perch = 0
        ##a## parent.values_dlm = [
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0,
        ##a##                     0
        ##a##                     ]
        parent.timeout_id = GLib.timeout_add(1000, update_gui, parent, dlm)
        print("timeout_add -",parent.timeout_id)
        #dlm.join()
    except Exception as e:
        end_t = time.time()
        print(f'Installation failed after {end_t - parent.start_t:.02f} seconds.'
                       f'The following exception occurred while waiting for the downloader to finish: {e!r}. '
                       f'Try restarting the process, the resume file will be used to start where it failed. '
                       f'If it continues to fail please open an issue on GitHub.')
        log_gtk(f'Installation failed after {end_t - parent.start_t:.02f} seconds.'
                       f'The following exception occurred while waiting for the downloader to finish: {e!r}. '
                       f'Try restarting the process, the resume file will be used to start where it failed. '
                       f'If it continues to fail please open an issue on GitHub.').show_all()

def post_dlm(main_window):
    #else:
    print("in post_dlm")
    main_window.end_t = time.time()
    if not main_window.args.no_install:
        # Allow setting savegame directory at install time so sync-saves will work immediately
        if main_window.game.supports_cloud_saves and main_window.args.save_path:
            main_window.igame.save_path = main_window.args.save_path

        postinstall = core.install_game(main_window.igame)
        if postinstall:
            cli._handle_postinstall(postinstall, main_window.igame, yes=main_window.args.yes)

        dlcs = core.get_dlc_for_game(main_window.game.app_name)
        if dlcs:
            print('The following DLCs are available for this main_window.game:')
            for dlc in dlcs:
                print(f' - {dlc.app_title} (App name: {dlc.app_name}, version: {dlc.app_version})')
            print('Manually installing DLCs works the same; just use the DLC app name instead.')

            install_dlcs = True
            if not main_window.args.yes:
                if not get_boolean_choice(f'Do you wish to automatically install DLCs?'):
                    install_dlcs = False

            if install_dlcs:
                _yes, _app_name = main_window.args.yes, app_name
                main_window.args.yes = True
                for dlc in dlcs:
                    app_name = dlc.app_name
                    self.install_game(main_window.args)
                main_window.args.yes, app_name = _yes, _app_name

        if main_window.game.supports_cloud_saves and not main_window.game.is_dlc:
            # todo option to automatically download saves after the installation
            #  main_window.args does not have the required attributes for sync_saves in here,
            #  not sure how to solve that elegantly.
            log_gtk(f'This main_window.game supports cloud saves, syncing is handled by the "sync-saves" command.To download saves for this main_window.game run "legendary sync-saves {main_window.game.app_name}"').show_all()

    old_igame = core.get_installed_game(main_window.game.app_name)
    if old_igame and main_window.args.repair_mode and os.path.exists(repair_file):
        if old_igame.needs_verification:
            old_igame.needs_verification = False
            core.install_game(old_igame)

        log_gtk('Removing repair file.').show_all()
        os.remove(repair_file)

    # check if install tags have changed, if they did; try deleting files that are no longer required.
    if old_igame and old_igame.install_tags != main_window.igame.install_tags:
        old_igame.install_tags = main_window.igame.install_tags
        log_gtk('Deleting now untagged files.').show_all()
        core.uninstall_tag(old_igame)
        core.install_game(old_igame)

    log_gtk(f'Finished installation process in {main_window.end_t - main_window.start_t:.02f} seconds.').show_all()

#
# launch
#
def launch_gtk(menu, app_names, parent):
    args = args_obj()
    app_name = app_names[0]
    app_title = app_names[1]
    igame = core.get_installed_game(app_name)
    if not igame:
        log_gtk(f'Game {app_name} is not currently installed!').show_all()
        print(f'Game {app_name} is not currently installed!')
        return 1

    if igame.is_dlc:
        log_gtk(f'{app_name} is DLC; please launch the base game instead!').show_all()
        print(f'{app_name} is DLC; please launch the base game instead!')
        return 1

    if not os.path.exists(igame.install_path):
        log_gtk(f'Install directory "{igame.install_path}" appears to be deleted, cannot launch {app_name}!').show_all()
        print(f'Install directory "{igame.install_path}" appears to be deleted, cannot launch {app_name}!')
        return 1

    if args.reset_defaults:
        log_gtk(f'Removing configuration section for "{app_name}"...').show_all()
        print(f'Removing configuration section for "{app_name}"...')
        core.lgd.config.remove_section(app_name)
        l.destroy()
        return

    # override with config value
    args.offline = core.is_offline_game(app_name) or args.offline
    if not args.offline:
        if not core.login():
            log_gtk('Login failed, cannot continue!').show_all()
            print('Login failed, cannot continue!')
            return 1

        if not args.skip_version_check and not core.is_noupdate_game(app_name):
            try:
                latest = core.get_asset(app_name, update=True)
            except ValueError:
                log_gtk(f'Metadata for "{app_name}" does not exist, cannot launch!').show_all()
                print(f'Metadata for "{app_name}" does not exist, cannot launch!')
                return 1

            if latest.build_version != igame.version:
                log_gtk('Game is out of date, please update or launch with update check skipping!').show_all()
                print('Game is out of date, please update or launch with update check skipping!')
                return 1

    params, cwd, env = core.get_launch_parameters(app_name=app_name, offline=args.offline,
                                                       extra_args=None, user=args.user_name_override,
                                                       #extra_args=extra, user=args.user_name_override,
                                                       wine_bin=args.wine_bin, wine_pfx=args.wine_pfx,
                                                       language=args.language, wrapper=args.wrapper,
                                                       disable_wine=args.no_wine,
                                                       executable_override=args.executable_override)

    if args.set_defaults:
        core.lgd.config[app_name] = dict()
        # we have to do this if-cacophony here because an empty value is still
        # valid and could cause issues when relying on config.get()'s fallback
        if args.offline:
            core.lgd.config[app_name]['offline'] = 'true'
        if args.skip_version_check:
            core.lgd.config[app_name]['skip_update_check'] = 'true'
        if extra:
            core.lgd.config[app_name]['start_params'] = shlex.join(extra)
        if args.wine_bin:
            core.lgd.config[app_name]['wine_executable'] = args.wine_bin
        if args.wine_pfx:
            core.lgd.config[app_name]['wine_prefix'] = args.wine_pfx
        if args.no_wine:
            core.lgd.config[app_name]['no_wine'] = 'true'
        if args.language:
            core.lgd.config[app_name]['language'] = args.language
        if args.wrapper:
            core.lgd.config[app_name]['wrapper'] = args.wrapper

    #print(f'Launching {app_name}...')
    #print(f'Launch parameters: {shlex.join(params)}')
    #print(f'Working directory: {cwd}')
    #if env:
    #    print('Environment overrides:', env)
    subprocess.Popen(params, cwd=cwd, env=env)

#
# dry launch
#
def dry_launch_gtk(menu, app_names, parent):
    args = args_obj()
    app_name = app_names[0]
    app_title = app_names[1]

    igame = core.get_installed_game(app_name)
    if not igame:
        log_gtk(f'Game {app_name} ({app_title}) is not currently installed!').show_all()
        print(f'Game {app_name} ({app_title}) is not currently installed!')
        return 1

    if igame.is_dlc:
        log_gtk(f'{app_name} ({app_title}) is DLC; please launch the base game instead!').show_all()
        print(f'{app_name} ({app_title}) is DLC; please launch the base game instead!')
        return 1

    if not os.path.exists(igame.install_path):
        log_gtk(f'Install directory "{igame.install_path}" appears to be deleted, cannot launch {app_name}!').show_all()
        print(f'Install directory "{igame.install_path}" appears to be deleted, cannot launch {app_name}!')
        return 1

    if args.reset_defaults:
        log_gtk(f'Removing configuration section for "{app_name} ({app_title})"...').show_all()
        print(f'Removing configuration section for "{app_name} ({app_title})"...')
        core.lgd.config.remove_section(app_name)
        l.destroy()
        return

    # override with config value
    args.offline = core.is_offline_game(app_name) or args.offline
    if not args.offline:
        if not core.login():
            log_gtk('Login failed, cannot continue!').show_all()
            print('Login failed, cannot continue!')
            return 1

        if not args.skip_version_check and not core.is_noupdate_game(app_name):
            try:
                latest = core.get_asset(app_name, update=True)
            except ValueError:
                log_gtk(f'Metadata for "{app_name}" ({app_title}) does not exist, cannot launch!').show_all()
                print(f'Metadata for "{app_name}" ({app_title}) does not exist, cannot launch!')
                return 1

            if latest.build_version != igame.version:
                log_gtk('Game is out of date, please update or launch with update check skipping!').show_all()
                print('Game is out of date, please update or launch with update check skipping!')
                return 1

    params, cwd, env = core.get_launch_parameters(app_name=app_name, offline=args.offline,
                                                       extra_args=None, user=args.user_name_override,
                                                       #extra_args=extra, user=args.user_name_override,
                                                       wine_bin=args.wine_bin, wine_pfx=args.wine_pfx,
                                                       language=args.language, wrapper=args.wrapper,
                                                       disable_wine=args.no_wine,
                                                       executable_override=args.executable_override)
    launch_dryrun_dialog = Gtk.MessageDialog(
                                        parent=parent,
                                        destroy_with_parent=True,
                                        message_type=Gtk.MessageType.INFO,
                                        buttons=Gtk.ButtonsType.OK,
                                        text=f'Launch parameters for {app_title}'
                                      )
    launch_dryrun_dialog.set_title(f"Launch parameters for {app_title}")
    launch_dryrun_dialog.set_default_size(400, 0)

    box_stats = launch_dryrun_dialog.get_content_area()
    box_stats.label = Gtk.Label(
        label=f'Launch parameters:\n{shlex.join(params)}\n\n'
              f'Working directory: {cwd}'
              #f'Environment overrides: {env}' if env else "" #TODO fix this
            )
    box_stats.label.set_max_width_chars(40)
    box_stats.label.set_line_wrap(True)
    box_stats.label.set_selectable(True)
    box_stats.label.set_margin_start(10)
    box_stats.label.set_margin_end(10)
    box_stats.add(box_stats.label)

    launch_dryrun_dialog.show_all()
    launch_dryrun_dialog_response = launch_dryrun_dialog.run()
    print(f'Not Launching {app_name} (dry run)')
    print(f'Launch parameters: {shlex.join(params)}')
    print(f'Working directory: {cwd}')
    if env:
        print('Environment overrides:', env)
    launch_dryrun_dialog.destroy()

#
# uninstall
#
def uninstall_gtk(menu, app_names, parent):
    app_name = app_names[0]
    app_title = app_names[1]
    igame = core.get_installed_game(app_name)
    if not igame:
        log_gtk(f'Game {app_name} not installed, cannot uninstall!').show_all()
        return 0
    if igame.is_dlc:
        log_gtk('Uninstalling DLC is not supported.').show_all()
        return 1
    uninstall_dialog = Gtk.MessageDialog(parent=parent,
                                        destroy_with_parent=True,
                                        message_type=Gtk.MessageType.QUESTION,
                                        buttons=Gtk.ButtonsType.OK_CANCEL,
                                        text=f'Do you wish to uninstall "{igame.title}"?'
                                      )
    uninstall_dialog.set_title(f"Uninstall {app_title}")
    uninstall_dialog.set_default_size(400, 0)
    uninstall_dialog_response = uninstall_dialog.run()
    if uninstall_dialog_response != Gtk.ResponseType.OK:
        uninstall_dialog.destroy()
        return 1
    uninstall_dialog.destroy()
    args = args_obj()
    
    try:
        # Remove DLC first so directory is empty when game uninstall runs
        dlcs = core.get_dlc_for_game(igame.app_name)
        for dlc in dlcs:
            if (idlc := core.get_installed_game(dlc.app_name)) is not None:
                print(f'Uninstalling DLC "{dlc.app_name}"...')
                l = log_gtk(f'Uninstalling DLC "{dlc.app_name}"...').show_all()
                core.uninstall_game(idlc, delete_files=not args.keep_files)
                l.destroy()

        print(f'Removing "{igame.title}" from "{igame.install_path}"...')
        l=log_gtk(f'Removing "{igame.title}" from "{igame.install_path}"...').show_all()
        core.uninstall_game(igame, delete_files=not args.keep_files, delete_root_directory=True)
        l.destroy()
        print('Game has been uninstalled.')
        log_gtk('Game has been uninstalled.').show_all()
        main_window.scroll.destroy()
        main_window.list_games()
    except Exception as e:
        print(f'Removing game failed: {e!r}, please remove {igame.install_path} manually.')
        log_gtk(f'Removing game failed: {e!r}, please remove {igame.install_path} manually.').show_all()

def list_files_gtk(menu, app_names, parent):
    args = args_obj()
    app_name = app_names[0]
    app_title = app_names[1]
    if args.platform_override:
        args.force_download = True

    if not args.override_manifest and not app_name:
        print('You must provide either a manifest url/path or app name!')
        return

    # check if we even need to log in
    if args.override_manifest:
        print(f'Loading manifest from "{args.override_manifest}"')
        manifest_data, _ = core.get_uri_manifest(args.override_manifest)
    elif core.is_installed(app_name) and not args.force_download:
        print(f'Loading installed manifest for "{app_name}"')
        manifest_data, _ = core.get_installed_manifest(app_name)
    else:
        print(f'Logging in and downloading manifest for {app_name}')
        if not core.login():
            print('Login failed! Cannot continue with download process.')
            log_gtk('Login failed! Cannot continue with download process.').show_all()
            return 1
        game = core.get_game(app_name, update_meta=True)
        if not game:
            print(f'Could not fetch metadata for "{app_name}" (check spelling/account ownership)')
            log_gtk(f'Could not fetch metadata for "{app_name}" (check spelling/account ownership)').show_all()
            return 1
        manifest_data, _ = core.get_cdn_manifest(game, platform_override=args.platform_override)

    manifest = core.load_manifest(manifest_data)
    files = sorted(manifest.file_manifest_list.elements,
                   key=lambda a: a.filename.lower())

    if args.install_tag:
        files = [fm for fm in files if args.install_tag in fm.install_tags]

    listfiles_dialog = Gtk.MessageDialog(
                                        parent=parent,
                                        destroy_with_parent=True,
                                        message_type=Gtk.MessageType.INFO,
                                        buttons=Gtk.ButtonsType.OK,
                                        text=f"List {app_title}'s files"
                                      )
    listfiles_dialog.set_title(f"List files for {app_title}")
    listfiles_dialog.set_default_size(600, 400)
    listfiles_dialog.set_resizable(True)
    box_main = listfiles_dialog.get_content_area()
    scrolled_window = Gtk.ScrolledWindow()
    box_main.add(scrolled_window)
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_hexpand(True)
    scrolled_window.set_vexpand(True)
    scrolled_window.label = Gtk.Label()
    scrolled_window.label.set_max_width_chars(60)
    scrolled_window.label.set_line_wrap(True)
    scrolled_window.label.set_selectable(True)
    scrolled_window.label.set_margin_start(10)
    scrolled_window.label.set_margin_bottom(0)
    scrolled_window.label.set_margin_top(0)
    scrolled_window.label.set_margin_end(10)
    scrolled_window.add(scrolled_window.label)

    if args.hashlist:
        for fm in files:
            print(f'{fm.hash.hex()} *{fm.filename}')
    elif args.csv or args.tsv:
        writer = csv.writer(stdout, dialect='excel-tab' if args.tsv else 'excel')
        writer.writerow(['path', 'hash', 'size', 'install_tags'])
        writer.writerows((fm.filename, fm.hash.hex(), fm.file_size, '|'.join(fm.install_tags)) for fm in files)
    elif args.json:
        _files = []
        for fm in files:
            _files.append(dict(
                filename=fm.filename,
                sha_hash=fm.hash.hex(),
                install_tags=fm.install_tags,
                file_size=fm.file_size,
                flags=fm.flags,
            ))
        print(json.dumps(_files, sort_keys=True, indent=2))
    else:
        install_tags = set()
        for fm in files:
            #print(fm.filename)
            scrolled_window.label.set_text(scrolled_window.label.get_text()+f"\n{fm.filename}")
            for t in fm.install_tags:
                install_tags.add(t)
        if install_tags:
            # use the log output so this isn't included when piping file list into file
            print(f'Install tags: {", ".join(sorted(install_tags))}')
            log_gtk(f'Install tags: {", ".join(sorted(install_tags))}').show_all()
    listfiles_dialog.show_all()
    listfiles_dialog_response = listfiles_dialog.run()
    listfiles_dialog.destroy()

def sync_saves_gtk(app_name, app_title, parent): pass

def verify_game_gtk(app_name, app_title, parent): pass

class main_window(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self,title="Legendary")
        #self.grid = Gtk.Grid(column_spacing=30, row_spacing=30)
        self.set_default_size(800, 600)
        self.box = Gtk.Box()
        self.add(self.box)
        self.bar_queue = MPQueue(-1)

        logged = False
        try:
            if core.login():
                logged = True
        except ValueError: pass
        except InvalidCredentialsError:
            print("Found invalid stored credentials")

        # 'Legendary' label
        self.legendary_label = Gtk.Label(label="Legendary")
        self.login_vbox = Gtk.VBox()
        self.login_vbox.pack_start(self.legendary_label, False, False, 10)

        # Login button
        if not logged:
            self.button_login = Gtk.Button(label="Login")
            self.button_login.connect("clicked", self.onclick_login)
            self.login_vbox.pack_start(self.button_login, False, False, 10)
        else:
            self.username_label = Gtk.Label(label=core.lgd.userdata["displayName"])
            self.button_logout = Gtk.Button(label="Logout")
            self.button_logout.connect("clicked", self.onclick_logout)
            self.login_vbox.pack_end(self.button_logout, False, False, 10)
            self.login_vbox.pack_end(self.username_label, False, False, 0)

        # Proress Bar for downloads
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.login_vbox.pack_end(self.progress_bar, False, False, 10)

        self.box.pack_start(self.login_vbox, False, False, 20)

        if logged:
            self.scroll = self.list_games()

        self.cmenu = Gtk.Menu.new()
        self.cmenu.app_name = ''
        self.cmenu.app_title = ''
        self.cmenu.app_s = [0,0]
        self.cmenu.launch      = Gtk.MenuItem.new_with_label('Launch')
        self.cmenu.dry_launch  = Gtk.MenuItem.new_with_label('Dry launch')
        self.cmenu.uninstall   = Gtk.MenuItem.new_with_label('Uninstall')
        self.cmenu.list_files  = Gtk.MenuItem.new_with_label('List files')
        self.cmenu.sync_saves  = Gtk.MenuItem.new_with_label('Sync saves')
        self.cmenu.verify_game = Gtk.MenuItem.new_with_label('Verify game')
        self.cmenu.launch     .connect('activate', launch_gtk, self.cmenu.app_s, self)
        self.cmenu.dry_launch .connect('activate', dry_launch_gtk, self.cmenu.app_s, self)
        self.cmenu.uninstall  .connect('activate', uninstall_gtk, self.cmenu.app_s, self)
        self.cmenu.list_files .connect('activate', list_files_gtk, self.cmenu.app_s, self)
        self.cmenu.sync_saves .connect('activate', sync_saves_gtk, self.cmenu.app_s, self)
        self.cmenu.verify_game.connect('activate', verify_game_gtk, self.cmenu.app_s, self)
        #self.cmenu.launch     .connect('activate', launch_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        #self.cmenu.dry_launch .connect('activate', dry_launch_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        #self.cmenu.uninstall  .connect('activate', uninstall_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        #self.cmenu.list_files .connect('activate', list_files_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        #self.cmenu.sync_saves .connect('activate', sync_saves_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        #self.cmenu.verify_game.connect('activate', verify_game_gtk, self.cmenu.app_name, self.cmenu.app_title, self)
        self.cmenu.append(self.cmenu.launch)
        self.cmenu.append(self.cmenu.dry_launch)
        self.cmenu.append(self.cmenu.uninstall)
        self.cmenu.append(self.cmenu.list_files)
        self.cmenu.append(self.cmenu.sync_saves)
        self.cmenu.append(self.cmenu.verify_game)


    def list_games(self):
        # Games
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_border_width(10)
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        self.box.pack_end(self.scroll, True, True, 0)
        self.scroll.games = Gtk.ListStore(str, str, str, str, str)
        gcols = ["appname","Title","Installed","Size","Update Avaiable"]

        # get games
        games, dlc_list = core.get_game_and_dlc_list()
        games = sorted(games, key=lambda x: x.app_title.lower())
        for citem_id in dlc_list.keys():
            dlc_list[citem_id] = sorted(dlc_list[citem_id], key=lambda d: d.app_title.lower())
        # add games to liststore for treeview
        for game in games:
            ls = (  game.app_name,
                    game.app_title,
                    is_installed(game.app_name),
                    installed_size(game.app_name),
                    update_avail(game.app_name),
                 )
            self.scroll.games.append(list(ls))
            #print(f' * {game.app_title} (App name: {game.app_name} | Version: {game.app_version})')
            for dlc in dlc_list[game.asset_info.catalog_item_id]:
                ls = (  dlc.app_name,
                        dlc.app_title+f" (DLC of {game.app_title})",
                        is_installed(dlc.app_name),
                        installed_size(dlc.app_name),
                        update_avail(dlc.app_name),
                     )
                self.scroll.games.append(list(ls))
                #print(f'  + {dlc.app_title} (App name: {dlc.app_name} | Version: {dlc.app_version})')

        # add games to treeview
        #self.scroll.gview = Gtk.TreeView(Gtk.TreeModelSort(model=self.scroll.games))
        self.scroll.gview = Gtk.TreeView(model=self.scroll.games)
        for i, c in enumerate(gcols): # from https://developer.gnome.org/gnome-devel-demos/stable/treeview_simple_liststore.py.html.en
            cell = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(c, cell, text=i)
            col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_sort_column_id(i)
            if c == "appname":
                col.set_visible(False)
            self.scroll.gview.append_column(col)

        self.scroll.gview.connect("row-activated", self.on_tree_selection_changed)
        self.scroll.gview.connect("button-press-event", self.context_menu)

        l = Gtk.Label()
        l.set_text("")
        g = Gtk.Grid()
        g.attach(self.scroll.gview, 0, 0, 1, 1)
        g.attach(l, 0, 1, 1, 1)
        self.scroll.add(g)
        return self.scroll

    def context_menu(self, selection, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            model, treeiter = selection.get_selection().get_selected()
            if treeiter is not None:
                self.cmenu.app_s[0] = self.cmenu.app_name = model[treeiter][0]
                self.cmenu.app_s[1] = self.cmenu.app_title = model[treeiter][1]
                print(self.cmenu.app_title,self.cmenu.app_name)

            self.cmenu.show_all()
            self.cmenu.popup_at_pointer()
            #print("ciao")
    def context_menu_destroy(parent): parent.cmenu.destroy()
        
    def onclick_login(self, widget):
        webbrowser.open('https://www.epicgames.com/id/login?redirectUrl=https%3A%2F%2Fwww.epicgames.com%2Fid%2Fapi%2Fredirect')
        exchange_token = ''
        sid = ask_sid(self)
        exchange_token = core.auth_sid(sid)
        if not exchange_token:
            log_gtk('No exchange token, cannot login.').show_all()
            return
        if core.auth_code(exchange_token):
            log_gtk(f'Successfully logged in as "{core.lgd.userdata["displayName"]}"').show_all()
        else:
            log_gtk('Login attempt failed, please see log for details.').show_all()
        self.destroy()
        main()

    def onclick_logout(self, widget):
        core.lgd.invalidate_userdata()
        log_gtk("Successfully logged out").show_all()
        self.destroy()
        main()

    def on_tree_selection_changed(self, selection, dummy1, dummy2):
        model, treeiter = selection.get_selection().get_selected()
        if treeiter is not None:
            install_gtk(model[treeiter][0], model[treeiter][1], self)
            #print(model[treeiter][0], model[treeiter][1])

def ask_sid(parent):
    dialog = Gtk.MessageDialog(parent=parent, destroy_with_parent=True, message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.OK_CANCEL)
    dialog.set_title("Enter Sid")
    #dialog.set_default_size(200, 200)

    label = Gtk.Label()
    label.set_markup("Please login via the epic web login, if web page did not open automatically, please manually open the following URL:\n<a href=\"https://www.epicgames.com/id/login?redirectUrl=https://www.epicgames.com/id/api/redirect\">https://www.epicgames.com/id/login?redirectUrl=https://www.epicgames.com/id/api/redirect</a>")
    entry = Gtk.Entry()
    box = dialog.get_content_area()
    box.pack_start(label, False, False, 0)
    box.add(entry)

    dialog.show_all()
    response = dialog.run()
    sid = entry.get_text()
    dialog.destroy()
    if response == Gtk.ResponseType.OK:
        return sid
    else:
        return 1

def main():
    win = main_window()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
