import sublime
import sublime_plugin

from Webos.webos import *

class WebosRunCommand(WebosCommand):

  def run(self, debug = False, *args):
    self.launch(debug,
      lambda s, d: self.output_message(d), 
      self.run_done)

  def run_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Completed in %.1f s]" % sender.elapsed)


class WebosPreviewCommand(WebosCommand):

  def run(self, open_in_browser = True, port = 0, *args):
    self.preview(
      open_in_browser, 
      port,
      lambda s, d: self.output_message(d), 
      self.debug_done)

  def debug_done(self, sender, exit_code, proc):
    if sender.result.find('Success'):
      self.output_message("[Completed in %.1f s]" % sender.elapsed)