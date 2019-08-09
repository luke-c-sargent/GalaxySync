from sync_with_galaxy.historyinstance import HistoryInstance
from sync_with_galaxy.libraryinstance import LibraryInstance

from bioblend.galaxy import GalaxyInstance

from datetime import datetime, timezone
import logging
import os

class GalaxySync:
  """
  NOTE: Requires both galaxy and the files to be mounted to be co-local to the script
  """
  def __init__(self, galaxy_address, api_key, mountpoint, library_name=None, library_description=None, history_name=None, loglevel=logging.ERROR):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=loglevel)
    logging.debug("Initializing GalaxySync with {}".format(galaxy_address))
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
    self._hi.add_library_contents(self._li.get_contents())