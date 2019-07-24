from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.histories import HistoryClient
from bioblend.galaxy.libraries import LibraryClient

import argparse
import os

# get arguments
parser = argparse.ArgumentParser()

parser.add_argument("-a", "--admin-api-key")
parser.add_argument("-s", "--server-address", default="127.0.0.1")
parser.add_argument("-p", "--port", default=80)
parser.add_argument("-m", "--mount-point", default="/mnt")

args = parser.parse_args()

#initialize bioblend Galaxy instance
galaxy_instance = GalaxyInstance(args.s+":"+args.p, args.a)
library_client = LibraryClient(galaxy_instance)
history_client = HistoryClient(galaxy_instance)

class LibraryInstance:
  def __init__(self, galaxy_instance, name, description):
    self._lc = LibraryClient(galaxy_instance)
    self._folder_ids = {}
    self._id = None
    self._name = name
    self._description = description
    self._contents = {} # { directory/path : { folder_id: "", file_contents: {...} } }
    self._initialize_library(self._name, self._description)

  def _initialize_library(self, name, description):
    if self._id:
      raise Exception("Error: library {} - id: {} already initialized".format(self._name, self._id))
    libraries = self.get_libraries(name)
    if not libraries:
      new_library_info = self._lc.create_library(name, description)
      self._id = new_library_info["id"]
      self._name = new_library_info["name"]
    elif len(libraries) != 1:
      raise Exception("ERROR: too many {} libraries found by get_or_create_library".format(name))

  @staticmethod
  def _prune_separators(input, leading=True, tailing=True, separator=os.sep):
    _l = len(separator)
    if input[-1*_l:] == separator:
      input = input[:-1*_l]
    if input[0:_l] == os.sep:
      input = input[_l:]
    return input

  # bioblend call wrapper method
  def get_libraries(self, name):
    return self._lc.get_libraries(name=name)
    
  def get_info(self):
    return {"id": self._id, "name": self._name}

  def get_contents(self):
    return self._contents

  def get_or_create_folder_path_id(self, path):
    if path = "":
      return None
    if path in self._contents.keys():
      return self._contents[path]["folder_id"]
    splitpath = path.split(os.sep)
    previous_id = None
    base = ""
    for dir in splitpath:
      if base != "":
        base += "/" + dir
      else:
        base = dir
      if base in self._contents.keys():
        previous_id = self._contents[base]["folder_id"]
      else:
        previous_id = self._lc.create_folder(self._id, dir, description=None, base_folder_id=previous_id)["id"]
        self._contents[base]["folder_id"] = previous_id
    return previous_id

  def add_file_batch(self, library_subdir, files_string):
    folder_id = None
    folder_id = self.get_or_create_folder_path_id(library_subdir)
    result = self._lc.upload_from_galaxy_filesystem(self._id, link_data_only="link_to_files")

  def add_files(self, files_generator, mountpoint_prefix): #from os.walk
    mountpoint_prefix = _prune_separators(mountpoint_prefix)
    for root, directories, files in files_generator:
      full_paths = ""
      for name in files:
        full_paths += os.path.join(root, name)+'\n'
      full_paths = full_path[:-1]
      library_subdir = _prune_separators(root)[len(mountpoint_prefix)+1:]
      file_info = add_file_batch(library_subdir, full_paths)

  def _create_subdir(name, base_folder_id):
    return self._lc.(self._id, name, base_folder_id=base_folder_id) 

  def create_folder(self, path):
    
    # sanitize path
    path = _prune_separators(path)
    chunked = path.split(os.sep)

def enumerate_files(entrypoint, subdirectory="by-filepath"):
  if entrypoint[-1:] == '/':
    entrypoint = entrypoint[:-1]
  full_path = entrypoint + "/{}".format(subdirectory)
  if os.path.isdir(full_path):
    return os.walk(full_path) # returns tuple of (root, directories, files)
  return ()

# create library if it doesnt exist
def get_or_create_library(name, description="Cohort data", library_client):

def 

def create_history(name, history_client):
  return history_client.create_history(name)

for root, directories, files in enumerate_files(args.m):
  # for each file
    # remove the mount point compo