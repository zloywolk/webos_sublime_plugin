
from Webos.exec import *

class AresProcess(AsyncProcess, ProcessListener):
  ARES_GENERATE = "ares-generate"
  ARES_PACKAGE = "ares-package"
  ARES_LAUNCH = "ares-launch"
  ARES_SERVER = "ares-server"
  ARES_SETUP_DEVICE = "ares-setup-device"
  ARES_INSPECT = "ares-inspect"
  ARES_INSTALL = "ares-install"

  def __init__(self, command, path = None, **kwargs):
    super().__init__(**kwargs)
    self.command = command
    self.path = path

  def run(self, shell_cmd = None, env = {}, **kwargs):
    super().run(self.command, shell_cmd, self.path, env, self, **kwargs)