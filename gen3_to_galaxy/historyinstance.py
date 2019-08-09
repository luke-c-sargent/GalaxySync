from bioblend.galaxy.histories import HistoryClient

import logging

class HistoryInstance:
  def __init__(self, galaxy_instance, name):
    logging.debug("Creating History instance {}".format(name))
    self._hc = HistoryClient(galaxy_instance)
    self._hdata = self._create_history(name)
    self._contents = {} # form: { file_id: {file_path: /a/b/c.txt, name: c.txt} ... }

  def _create_history(self, name):
    return self._hc.create_history(name)
  
  def get_id(self):
    return self._hdata["id"]
    
  def get_name(self):
    return self._hdata["name"]

  def add_library_contents(self, contents):
    library_file_ids = []
    for folder in contents:
      file_dict = contents[folder]["files"]
      for file in file_dict:
        library_file_ids.append(file_dict[file])
    logging.debug("adding files to history {}: \n - {}".format(self.get_name(), library_file_ids))
    for lib_file in library_file_ids:
      txt = ""
      results = self._hc.upload_dataset_from_library(self.get_id(), lib_file)
      self._contents[results["id"]] = {"file_path" : results["file_name"], "name": results["name"]}
      print(self._contents)