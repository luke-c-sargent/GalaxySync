from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.histories import HistoryClient
from bioblend.galaxy.libraries import LibraryClient

from datetime import datetime, timezone

import argparse
import logging
import os

class Gen3GalaxySync:
  """
  NOTE: Requires both galaxy and the files to be mounted to be co-local to the script
  """
  def __init__(self, galaxy_address, api_key, mountpoint, library_name=None, library_description=None, history_name=None, loglevel=logging.ERROR):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=loglevel)
    logging.debug("Initializing Gen3GalaxySync with {}".format(galaxy_address))
    mountpoint = os.path.abspath(mountpoint)
    # set default values for omitted arguments
    if not library_name:
      library_name = mountpoint[mountpoint.rfind(os.sep)+1:] or "root"
    if not library_description:
      library_description = "Library created from specified local mount point"
    if not history_name:
      history_name = library_name + " @ " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    self._gi = GalaxyInstance(galaxy_address, api_key)
    self._li = LibraryInstance(self._gi, library_name, library_description, mountpoint)
    self._hi = HistoryInstance(self._gi, history_name)

class HistoryInstance:
  def __init__(self, galaxy_instance, name):
    logging.debug("Creating History instance {}".format(name))
    self._hc = HistoryClient(galaxy_instance)
    self._hdata = self._create_history(name)

  def _create_history(self, name):
    r = self.create_history(name)

class LibraryInstance:
  def __init__(self, galaxy_instance, name, description, entrypoint):
    logging.debug("Creating Library instance {} - {}".format(name, description))
    self._lc = LibraryClient(galaxy_instance)
    self._folder_ids = {}
    self._id = None
    self._name = name
    self._description = description
    self._entrypoint = entrypoint
    self._contents = {} # { directory/path : { folder_id: "", files: {...} } }
    # initialize a library, creating 
    self._initialize_library(self._name, self._description, self._entrypoint)

  def file_in_library(self, full_path):
    if not full_path.startswith(self._entrypoint):
      return False
    rsep_idx = full_path.rfind(os.sep)
    dir_key = full_path[len(_entrypoint):rsep_idx]
    if dir_key in self._contents.keys():
      filename = full_path[rsep_idx+1:]
      if filename in self._contents[dir_key]["files"].keys():
        return True
    return False

  def _initialize_library(self, name, description, entrypoint):
    # check if the library has already been initialized
    if self._id:
      raise Exception("Error: library {} - id: {} already initialized".format(self._name, self._id))
    # check to see if a library of the same name exists in Galaxy already
    libraries = self.get_libraries(name)
    if not libraries:
      logging.debug("No existing library '{}' found, creating".format(name))
      new_library_info = self._lc.create_library(name, description)
      self._id = new_library_info["id"]
      self._name = new_library_info["name"]
      self._contents = {
        "/" : { "folder_id" : None, "files" : {}
        }
      }
    elif len(libraries) != 1: # if there is more than 1 library of name 'name' -- this shouldn't happen
      raise Exception("ERROR: too many {} libraries found by get_or_create_library".format(name))
    # check for extant files and folders
    else:
      self._id = libraries[0]["id"]
      self._name = libraries[0]["name"]
      logging.debug("Existing library '{} : {}' found, enumerating contents".format(self._name, self._id))
      self._enumerate_existing_library_files()
    self.add_files(entrypoint)

  def _enumerate_existing_library_files(self):
    library_contents = self._lc.get_folders(self._id)
    file_list = []
    # ensure the folders and their contents are initialized, then add files to their respective contents
    for item in library_contents:
      if item["type"] == "folder":
        if item["name"] not in self._contents.keys():
          self._contents[item["name"]] = {"folder_id": None}
        self._contents[item["name"]]["folder_id"] = item["id"]
        self._contents[item["name"]]["files"] = {}
      elif item["type"] == "file":
        file_list.append(item)
      else:
        logging.warn("Library content item {} is neither file nor folder, but {}".format(item["name"], item["type"]))
      for f in file_list:
        base_dir = f["name"][:f["name"].rfind('/')] or "/"
        fname = f["name"][f["name"].rfind('/')+1:]
        self._contents[base_dir]["files"][fname] = f["id"]
    logging.debug("File contents after enumerating existing files:\n{}".format(self._contents))

  # bioblend call wrapper method
  def get_libraries(self, name):
    return self._lc.get_libraries(name=name)
    
  def get_library_info(self):
    return {"id": self._id, "name": self._name}

  def get_contents(self):
    return self._contents

  def get_or_create_folder_path_id(self, path):
    if path == "/":
      return None
    if path in self._contents.keys():
      return self._contents[path]["folder_id"]
    splitpath = path.split(os.sep)
    previous_id = None
    base = ""
    for dir in splitpath[1:]:
      base += "/"+dir
      if base in self._contents.keys():
        previous_id = self._contents[base]["folder_id"]
      else:
        previous_id = self._lc.create_folder(self._id, dir, description=None, base_folder_id=previous_id)["id"]
        self._contents[base]["folder_id"] = previous_id
        self._contents[base]["files"] = {}
    return previous_id

  def add_file_batch(self, library_subdir, files_string):
    folder_id = None
    folder_id = self.get_or_create_folder_path_id(library_subdir)
    result = self._lc.upload_from_galaxy_filesystem(self._id, link_data_only="link_to_files")
    #TODO - add file metadata to content
    print(result)

  def add_files(self, entrypoint):
    entrypoint_iterator = self._filepath_enumerator(entrypoint)
    # go through files and folders
    for root, directories, files in files_generator:
      log.debug("adding files from {} to library {}:{}".format(root, self._id, self._name))
      full_paths = ""
      for name in files:
        log.debug("adding file {}".format(name))
        full_path = os.path.join(root, name)
        if not self.file_in_library(full_path=full_path):
          full_paths += full_path+'\n'
        else:
          logging.debug("{} found in library already; not adding".format(full_path))
      full_paths = full_paths[:-1]
      library_subdir = root[len(entrypoint):]
      file_info = add_file_batch(library_subdir, full_paths)

  def _filepath_enumerator(self, entrypoint):
    if os.path.isdir(entrypoint):
      return os.walk(entrypoint) # returns tuple of (root, directories, files)
    raise Exception("{} is not a valid path to traverse".format(entrypoint))

