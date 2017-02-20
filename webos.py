import json
import os
import sublime
import sublime_plugin

from Webos.ares import *

class WebosCommand(sublime_plugin.WindowCommand):
  webos_settings = "Webos.sublime-settings"
  output_view = None

  def is_debug(self):
    settings = sublime.load_settings(self.webos_settings)
    if settings and settings.get("debug"):
      return settings.get("debug")
    return False

  def get_cli_path(self):
    settings = sublime.load_settings(self.webos_settings)
    if settings and settings.get("cli_path"):
      return settings.get("cli_path")
      
  def get_projects_dir(self):
    settings = sublime.load_settings(self.webos_settings)
    if settings and settings.get("projects_dir"):
      return settings.get("projects_dir")

  def get_default_target(self):
    settings = sublime.load_settings(self.webos_settings)
    if settings and settings.get("target"):
      return settings.get("target")

  def add_app_to_project(self, app_path):
    d = self.window.project_data()

    if not d:
      d = {"folders": [{
                        "path": app_path, 
                        "follow_symlinks": True}]
                      }
    else:
      d["folders"].append({"path": app_path, "follow_symlinks": True})
      
    self.window.set_project_data(d)

  def create_output_panel(self):
    WebosCommand.output_view = self.window.create_output_panel("webos")
    WebosCommand.output_view.settings().set("line_numbers", False)
    WebosCommand.output_view.settings().set("gutter", False)
    WebosCommand.output_view.settings().set("scroll_past_end", False)
    WebosCommand.output_view.set_read_only(True)

    self.window.create_output_panel("webos")

  def show_output_view(self):
    if not WebosCommand.output_view:
      self.create_output_panel()
    self.window.run_command("show_panel", {"panel": "output.webos"})  
  
  def output_message(self, message):
    self.show_output_view()

    WebosCommand.output_view.run_command(
            'append',
            {'characters': "%s\n" % message, 'force': True, 'scroll_to_end': True})

  def get_appinfo_path(self, current_file = None):
    if not current_file:
      current_file = self.window.active_view().file_name()

    app_path = os.path.dirname(current_file)

    while True:
      parent = os.path.dirname(app_path)
      if parent == app_path:
        break
      
      if os.path.exists(os.path.join(app_path, "appinfo.json")):
        return app_path
      else:
        app_path = parent

    return None

  def get_appinfo(self, appinfo_path = None):
    if not appinfo_path:
      appinfo_path = self.get_appinfo_path()

    if not appinfo_path:
      return None

    with open(os.path.join(appinfo_path, "appinfo.json"), 'rt') as fd:
      return json.load(fd)

  def create(self, app_type = "webapp", create_process_callback = None, create_done_callback = None):
    # TODO: create app
    pass

  def preview(self, open_in_browser = True, port = 0, preview_process_callback = None, preview_done_callback = None):
    app_dir = self.get_appinfo_path(self.window.active_view().file_name())
    if not app_dir:
        self.output_message("Error: Could not find appinfo.json")
        return

    command = [AresProcess.ARES_SERVER]

    if port != 0:
      command.extend(["-p", port])

    if open_in_browser:
      command.append("-o")

    if self.is_debug():
      command.append("-v")

    command.append(app_dir)

    preview_proc = AresProcess(command,
      path= self.get_cli_path(),
      on_data_callback = preview_process_callback,
      on_done_callback = preview_done_callback)

    preview_proc.run(message = "Running local web-server")

  def package(self, mode = None, package_process_callback = None, package_done_callback = None):
    if mode:
      if mode == "no-minify":
        package_mode = "--no-minify"
      elif mode == "rom":
        package_mode = "--rom"
    else:
      package_mode = None

    app_dir = self.get_appinfo_path(self.window.active_view().file_name())
    if not app_dir:
        self.output_message("Error: Couldn't find appinfo.json")
        return

    command = [AresProcess.ARES_PACKAGE,
                    app_dir,
                    "-o", app_dir]

    if not package_mode is None:
      command.append(package_mode)

    # verbose mode in debug
    if self.is_debug():
        command.append("-v")

    package_proc = AresProcess(command, 
      path = self.get_cli_path(),
      on_data_callback = package_process_callback,
      on_done_callback = package_done_callback)
      

    app_id = self.get_appinfo()["id"]

    package_proc.run(message = "Packaging %s with mode %s..." % (app_id, mode),
        working_dir = app_dir)

  def install(self, install_process_callback = None, install_done_callback = None):
    app_dir = self.get_appinfo_path(self.window.active_view().file_name())
    if not app_dir:
      self.output_message("Error: Couldn't find appinfo.json")
      return

    app_info = self.get_appinfo()
    if not app_info:
      self.output_message("Error: Couldn't retrieve data from %s" % os.path.join(app_dir, "appinfo.json"))
      return

    ipk = "%s_%s_all.ipk" % (app_info["id"], app_info["version"])
    target = self.get_default_target()

    if not target:
      self.output_message("Error while read plugin serttings: Couldn't find default target")

    command = [AresProcess.ARES_INSTALL, "-d", target, ipk]

    if self.is_debug():
      command.append("-v")

    install_proc = AresProcess(command, 
      path = self.get_cli_path(),
      on_data_callback = install_process_callback,
      on_done_callback = install_done_callback)

    install_proc.run(message = "Installing %s into %s" % (ipk, target),
      working_dir = app_dir)

  def launch(self, debug = False, launch_process_callback = None, launch_done_callback = None):

    app_dir = self.get_appinfo_path(self.window.active_view().file_name())
    if not app_dir:
      self.output_message("Error: Couldn't find appinfo.json")
      return

    app_info = self.get_appinfo()
    if not app_info:
      self.output_message("Error: Couldn't retrieve data from %s" % os.path.join(app_dir, "appinfo.json"))
      return

    target = self.get_default_target()

    if not target:
      self.output_message("Error while read plugin serttings: Couldn't find default target")

    command = [AresProcess.ARES_LAUNCH, "-d", target, app_info["id"]]

    if self.is_debug():
      command.append("-v")

    if (debug):
      command.extend(["-i", "-o"])

    launc_proc = AresProcess(command, 
      path = self.get_cli_path(),
      on_data_callback = launch_process_callback,
      on_done_callback = launch_done_callback)

    if (debug):
      message = "Debugging the application %s on %s" % (app_info["id"], target)
    else:
      message = "Running the application %s on %s" % (app_info["id"], target)

    launc_proc.run(message = message,
      working_dir = app_dir)

class WebosShowOutputViewCommand(WebosCommand):
  def run(self):
    self.show_output_view()