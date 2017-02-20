import os

import sublime
import sublime_plugin

from Webos.webos import *
from Webos.ares import *

# DONE: Web Application
# TODO: JS Service
# TODO: appinfo.json

class WebosCreateApplicationCommand(WebosCommand):
  template_list = []
  selected_index = -1
  app_path = ""

  def run(self):
    command = [AresProcess.ARES_GENERATE, "-l", "webapp"]
    
    if self.is_debug():
      command.append("-v")

    templates_proc = AresProcess(command, 
      path = self.get_cli_path(),
      on_done_callback = self.on_templates_done)
    templates_proc.run(message = "Get available templates")

  def on_templates_done(self, sender, exit_code, proc):
    if not sender.result or not isinstance(sender.result, str):
      return

    self.template_list.clear()
    bootplates = (bootplate.split(' ') for bootplate in sender.result.split('\n') if bootplate)
    for bootplate in bootplates:
      self.template_list.append(bootplate[0])

    self.window.show_quick_panel(self.template_list, self.get_application_name)

  def get_application_name(self, index):
    if index != -1:
      self.selected_index = index
      self.window.show_input_panel('Input your application name: ', 
        'sampleapp', 
        self.create_appliacation,
        None,
        None)

  def create_appliacation(self, name):
    if not name or name == "":
      return

    app_name = name
    app_info = {
                  "id": "com.mydomain.%s" % app_name,
                  "version": "0.0.1",
                  "icon": "icon.png",
                  "type": "web",
                  "title": "App title",
                }

    template = self.template_list[self.selected_index]
    self.app_path = os.path.join(self.get_projects_dir(), app_name)
    command = [AresProcess.ARES_GENERATE,
               "-t", template,
               "-f",
               "-p", json.dumps(app_info),
               self.app_path]

    if self.is_debug():
      command.append("-v")

    create_proc = AresProcess(command,
      path = self.get_cli_path(),
      on_done_callback = self.on_create_done, 
      on_data_callback = self.on_create_process)
    create_proc.run(message = "Create %s application in %s" % (template, self.app_path))

  def on_create_process(self, sender, data):
    self.output_message(data)

  def on_create_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Completed in %.1f s]" % sender.elapsed)
      self.add_app_to_project(self.app_path)
      self.window.open_file("%s/appinfo.json" % self.app_path)