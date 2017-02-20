import threading
import time
import os
import sys
import subprocess
import functools

import sublime
import sublime_plugin

def decode(data, encoding):
  try:
    characters = data.decode(encoding)
  except:
    characters = "[Decode error - output not " + encoding + "]\n"
    proc = None
  
  characters = characters.replace('\r\n', '\n').replace('\r', '\n').strip()
  return characters

class ProcessListener(object):
  def __init__(self, 
      on_data_callback = None,
      on_done_callback = None, 
      on_error_callback = None):

    self.on_done_callback = on_done_callback
    self.on_data_callback = on_data_callback
    self.on_error_callback = on_error_callback
    
    self.result = ""
    self.elapsed = 0.0

  def on_data(self, proc, data):
    self.result += decode(data, 'utf-8')
    if self.on_data_callback:
      self.on_data_callback(self, decode(data, 'utf-8'))

  def on_done(self, proc):
    self.elapsed = time.time() - proc.start_time
    exit_code = proc.exit_code()

    if exit_code == 0 or exit_code is None:
      if self.on_done_callback:
        self.on_done_callback(self, exit_code, proc)
    else: 
      if self.on_error_callback:
        self.on_error_callback(self, exit_code, proc)

class AsyncProcessProgress(object):
  def __init__(self, proc, message, success_message = ""):
    self.proc = proc
    if message == "":
      self.message = "Process"
    else:
      self.message = message
    self.success_message = success_message
    self.add_end = 1
    self.size = 8
    sublime.set_timeout(lambda: self.run(0), 100)

  def run(self, i):
    if not self.proc.poll():
      return

    before = i % self.size
    after = (self.size - 1) - before

    sublime.status_message("\r%s [%s=%s] %.1fs " % 
      (self.message, ' ' * before, ' ' * after, time.time() - self.proc.start_time))

    if not after:
      self.add_end = -1
    if not before:
      self.add_end = 1

    i += self.add_end

    sublime.set_timeout(lambda: self.run(i), 100)

class AsyncProcess(object):
 
  def run(self, 
           cmd, 
           shell_cmd,
           path = "",
           env = {}, 
           listener = None,
           shell = True, 
           working_dir = None,
           stdin = subprocess.PIPE, 
           stdout = subprocess.PIPE, 
           stderr = subprocess.PIPE,
           progress = True,
           message = "",
           success_message = ""):

    if not shell_cmd and not cmd:
      raise ValueError("shell_cmd or cmd is required")
    
    if shell_cmd and not isinstance(shell_cmd, str):
      raise ValueError("shell_cmd must be a string")

    startupinfo = None
    if os.name == "nt":
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if path:
      old_path = os.environ["PATH"]
      os.environ["PATH"] += ";%s" % os.path.expandvars(path)

    self.proc_env = os.environ.copy()
    self.proc_env.update(env)

    for k, v in self.proc_env.items():
      self.proc_env[k] = os.path.expandvars(v)

    self.listener = listener

    try:

      if shell_cmd:
        print("Executing %s" % shell_cmd)
      elif cmd:
        print("Executing %s" % " ".join(cmd))

      if working_dir:
        os.chdir(os.path.expandvars(working_dir))

      self.start_time = time.time()

      if shell_cmd and sys.platform == "win32":
        self.proc = subprocess.Popen(shell_cmd,
                                   stdout = stdout,
                                   stderr = stderr,
                                   stdin = stdin,
                                   startupinfo = startupinfo,
                                   env = self.proc_env,
                                   shell = True)
      else:
        self.proc = subprocess.Popen(cmd,
                                   stdout = stdout,
                                   stderr = stderr,
                                   stdin = stdin,
                                   startupinfo = startupinfo,
                                   env = self.proc_env,
                                   shell = True)

      if progress:
        AsyncProcessProgress(self, message, success_message)

    except Exception as e:
      print(str(e))

    if path:
      os.environ["PATH"] = old_path

    if (self.proc.stdout):
      threading.Thread(target=self.read_stdout).start()

    if (self.proc.stderr):
      threading.Thread(target=self.read_stderr).start()

  def poll(self):
    return self.proc.poll() is None

  def exit_code(self):
    return self.proc.poll()

  def read_stdout(self):
      while True:
        data = os.read(self.proc.stdout.fileno(), 2**15)
        
        if len(data) > 0:
          if self.listener:
            self.listener.on_data(self, data)
        else:
          self.proc.stdout.close()
          if (self.listener):
            self.listener.on_done(self)
          break

  def read_stderr(self):
    while True:
      data = os.read(self.proc.stderr.fileno(), 2**15)
        
      if len(data) > 0:
        if self.listener:
          self.listener.on_data(self, data)
      else:
        self.proc.stderr.close()
        break