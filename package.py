import sublime
import sublime_plugin

from Webos.webos import *

class WebosPackageCommand(WebosCommand):

  def run(self, mode = None, *args):
    self.package(mode, lambda s, d: self.output_message(d), self.package_done)

  def package_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
        self.output_message("[Completed in %.1f s]" % sender.elapsed)
    