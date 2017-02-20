import sublime
import sublime_plugin

from Webos.webos import *

class WebosInstallCommand(WebosCommand):
  _launch = False
  _debug = False

  def run(self, package = False, launch = False, package_mode = None, debug = False, *args):
    self._launch = launch
    self._debug = debug

    if package:
      self.package(mode = package_mode,
          package_process_callback = lambda s, d: self.output_message(d),
          package_done_callback = self.package_done)
    else:
      self.install(
          install_process_callback = lambda s, d: self.output_message(d),
          install_done_callback = self.install_done)

  def package_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Package completed in %.1f s]" % sender.elapsed)
      self.install(
          install_process_callback = lambda s, d: self.output_message(d),
          install_done_callback = self.install_done)

  def install_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Install completed in %.1f s]" % sender.elapsed)
      if self._launch:
        self.launch(
          self._debug,
          launch_process_callback = lambda s, d: self.output_message(d),
          launch_done_callback = self.launch_done)

  def launch_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Launch completed in %.1f s]" % sender.elapsed)


