# Gen3 -> Galaxy
Taking a vanilla Galaxy instance and configuring it for a particular user with data provisioned by gen3

init steps:
- have a vanilla galaxy instance
- create admin user 
- create remote user w/ api key
- use remote_user headers to log user in
- add `gen3-fuse`-populated files to library
- add library files to history
- make that the active history

persist steps:
- store user API key -- somehow

requirements:
1. bioblend