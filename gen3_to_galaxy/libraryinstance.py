from bioblend.galaxy.libraries import LibraryClient

import os
import logging

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
    logging.debug("Checking for {} in library".format(full_path))
    if not full_path.startswith(self._entrypoint):
      logging.debug("FIL: {} doesn't start with {}".format(full_path, self._entrypoint))
      return False
    rsep_idx = full_path.rfind(os.sep)
    dir_key = full_path[len(self._entrypoint):rsep_idx]
    if not dir_key:
      dir_key = os.sep
    if dir_key in self._contents.keys():
      filename = full_path[rsep_idx+1:]
      if filename in self._contents[dir_key]["files"].keys():
        logging.debug("FIL: {} in {}".format(filename, self._contents[dir_key]["files"].keys()))
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
    library_contents = self._lc.show_library(self._id, contents=True)
    file_list = []
    # ensure the folders and their contents are initialized, then add files to their respective contents
    if logging.root.level == logging.DEBUG:
      txt=""
      for lc in library_contents:
        txt+= str(lc) + "\n"
      logging.debug("Galaxy library contents: {} items\n{}".format(len(library_contents), txt))
    for item in library_contents:
      logging.debug("ANALYZING ITEM {}".format(item))
      if item["type"] == "folder":
        logging.debug("\t- Found FOLDER {} : {}".format(item["name"], item["id"]))
        if item["name"] not in self._contents.keys():
          self._contents[item["name"]] = {"folder_id": None}
        self._contents[item["name"]]["folder_id"] = item["id"]
        self._contents[item["name"]]["files"] = {}
      elif item["type"] == "file":
        logging.debug("\t- Found FILE {} : {}".format(item["name"], item["id"]))
        file_list.append(item)
      else:
        logging.warn("Library content item {} is neither file nor folder, but {}".format(item["name"], item["type"]))
    for f in file_list:
      base_dir = f["name"][:f["name"].rfind('/')] or "/"
      fname = f["name"][f["name"].rfind('/')+1:]
      if fname in self._contents[base_dir]["files"].keys():
        logging.debug("file {} already in contents with id {}".format(f["name"], f["id"]))
        continue
      self._contents[base_dir]["files"][fname] = f["id"]
    if logging.root.level == logging.DEBUG:
      txt=""
      for lc in self._contents:
        txt+= "\t" + lc + ": {}\n".format(self._contents[lc])
      logging.debug("File contents after enumerating existing files:\n{}".format(txt))

  # bioblend call wrapper method
  def get_libraries(self, name):
    # fix bioblend error since my PR merger hasn't made it into a release yet :(
    # https://github.com/galaxyproject/bioblend/pull/273
    result = self._lc.get_libraries(name=name, deleted=False)
    return list([x for x in result if not x["deleted"]])
    
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
        previous_id = self._lc.create_folder(self._id, dir, description=None, base_folder_id=previous_id)[0]["id"]
        self._contents[base] = {}
        self._contents[base]["folder_id"] = previous_id
        self._contents[base]["files"] = {}
        logging.debug("created folder {} with id {}".format(base, previous_id))
    return previous_id

  def add_file_batch(self, library_subdir, files_string):
    folder_id = self.get_or_create_folder_path_id(library_subdir)
    logging.debug("UPLOADING files:\n{}".format(files_string))
    result = self._lc.upload_from_galaxy_filesystem(self._id, filesystem_paths=files_string, folder_id=folder_id, link_data_only="link_to_files")
    for _r in result:
      filename = _r["name"]
      self._contents[library_subdir]["files"][_r["name"]] = _r["id"]
      logging.debug("\tADDED file to local contents: {} - {}".format(filename, self._contents[library_subdir]["files"][_r["name"]]))

  def add_files(self, entrypoint):
    entrypoint_iterator = self._filepath_enumerator(entrypoint)
    # go through files and folders
    for root, directories, files in entrypoint_iterator:
      full_paths = ""
      for name in files:
        logging.debug("considering adding file {}...".format(name))
        full_path = os.path.join(root, name)
        if not self.file_in_library(full_path=full_path):
          full_paths += full_path+'\n'
        else:
          logging.debug("{} found in library already; not adding".format(full_path))
      if full_paths:
        logging.debug("Adding files: \n{}".format(full_paths))
        full_paths = full_paths[:-1]
        library_subdir = root[len(entrypoint):] or "/"
        file_info = self.add_file_batch(library_subdir, full_paths)

  def _filepath_enumerator(self, entrypoint):
    if os.path.isdir(entrypoint):
      return os.walk(entrypoint) # returns tuple of (root, directories, files)
    raise Exception("{} is not a valid path to traverse".format(entrypoint))