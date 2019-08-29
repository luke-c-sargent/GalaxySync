from bioblend.galaxy.histories import HistoryClient

from datetime import datetime, timezone

import logging

class HistoryInstance:

  DEFAULT_TAG = "GalaxySynced"
  DATETIME_TEMPLATE = "%Y-%m-%d %H:%M:%S UTC"
  DATETIME_REGEX = '20[0-9]{2}-\d\d-\d\d \d\d:\d\d:\d\d UTC'

  def __init__(self, galaxy_instance, name, contents):
    # initialize the History client
    self._hc = HistoryClient(galaxy_instance)
    self._timestamp = datetime.now(timezone.utc).strftime(self.DATETIME_TEMPLATE)
    self._library_name = name
    self._contents = {} # form: { file_id: {file_path: /a/b/c.txt, name: c.txt} ... }
    self._tags = []

    # check for existing histories
    extant_history = self._check_for_extant_history()
    if extant_history: # populate the object if there is a history
      self._id = extant_history["id"]
      self._name = extant_history["name"]
      self._enumerate_existing_history_files()
      self._sync_with_extant_history(extant_history, contents)
    else: # create the history fresh
      history_name = self.get_timestamped_name()
      logging.debug("Creating History instance {}".format(history_name))
      hdata = self._create_history(history_name)
      self._id = hdata["id"]
      self._name = hdata["name"]
      logging.debug("Adding contents to history {}...".format(history_name))
      logging.debug("".join(" - {}: {}\n".format(x, contents[x]) for x in contents))
      self.add_library_contents(contents)
      logging.debug("Tagging history with values '{}' and '{}'".format(self.DEFAULT_TAG, self._timestamp))
      self.tag_history(self.DEFAULT_TAG)
      self.tag_history(self._timestamp)

  def _sync_with_extant_history(self, library_contents):
    # get difference between extant contents and provided contents
    contents_diff = self._prune_extant_contents(library_contents)
    self.add_library_contents(contents_diff)

  def _prune_extant_contents(self, library_contents):
    # sub-routine for checking history
    def in_history_contents(f_id):
      for hc in self._contents:
        if self._contents[hc]["dataset_id"] == f_id:
          return True
      return False
    # takes contents from history, have a mutable contents to ... mutate
    lib_contents_mutable = dict(library_contents)
    # compare the two lists
    for lc in library_contents:
      file_list = library_contents[lc]["files"]
      for f in file_list:
        f_id = file_list[f]
        if in_history_contents(f_id):
          del lib_contents_mutable[lc]["files"][f]
    # return the difference
    return lib_contents_mutable

  def _check_for_extant_history(self):
    """
    returns `None` if no extant history, else dict:
    {
      "name" : ...,
      "id" : ...,
      "tags" : ...,
      "datetime_tag" : ...
    }
    """
    # for each history entry,
    extant_histories = []
    chosen_history = None
    found_histories = self._hc.get_histories(name=self._name, deleted=False)
    if not found_histories:
      logging.debug("no histories found with name {}".format(self._name))
      return None
    for eh in found_histories:
      # get: name, id, deleted, tags [] ...
      if self.DEFAULT_TAG in eh["tags"] and eh["name"].startswith(self._name):
        # candidate's key features:
        datetime_tag = None
        for _tag in eh["tags"]:
          if self._check_tag_for_timestamp(_tag):
            datetime_tag = _tag
            break
        simplified_eh = {
          "name": eh["name"],
          "id": eh["id"],
          "tags": eh["tags"],
          "datetime_tag": datetime_tag
        }
        extant_histories.append(simplified_eh)
    eh_len = len(extant_histories)
    if eh_len > 1: #disambiguate histories
      logging.warn("Multiple generated histories found with prefix {}:\n-".format(self._name))
      for eh in extant_histories:
        logging.warn("\t- {} : {}".format(eh["name"], eh["id"]))
      return self._disambiguate_multiple_extant_histories(extant_histories)
    elif eh_len == 1:
      return {"id": extant_histories[0]["id"], "name": extant_histories[0]["name"]}
    elif eh_len == 0:
      return None


  def _disambiguate_multiple_extant_histories(self, extant_histories):
      extant_histories = sorted(extant_histories, key=lambda i: i["datetime_tag"], reverse=True)
      chosen_history = extant_histories[0]
      # log the incongruity
      logging.warn("...picking newest history:\n\t- {} : {}".format(chosen_history["id"], chosen_history["name"]))
      return {"id": chosen_history["id"], "name": chosen_history["name"]}

  def _create_history(self, name):
    return self._hc.create_history(name)

  def tag_history(self, tag):
    if self._id:
      self._hc.create_history_tag(self._id, tag)
    else:
      raise Exception("cannot create history tag when history id is None")

  def _check_tag_for_timestamp(self, tag):
    return re.match(SELF.DATETIME_REGEX, tag) != None

  def _enumerate_existing_history_files(self):
    for i in self._hc.show_history(self._id, contents=True, deleted=False):
      self._contents[i["name"]] = {
        "file_name" : i["file_name"],
        "dataset_id" : i["dataset_id"]
      }

  def get_timestamped_name(self):
    if timestamped:
      return "{} @ {}".format(self._name, self._timestamp)
    return self._name

  def get_id(self):
    return self._id

  def get_name(self):
    return self._name

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