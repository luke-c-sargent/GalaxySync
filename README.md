# GalaxySync
Taking a 'clean' [Galaxy](https://galaxyproject.org/) instance and provisioning it with data

requirements:
- [Galaxy](https://github.com/galaxyproject/galaxy)
- bioblend
  - `$ pip install -r requirements.txt`

given:
- a local Galaxy instance
- an admin API key for the Galaxy instance
- a directory containing one or more files accessible to Galaxy
  - this directory will be crawled recursively to files in all subdirectories

...a user can use the `galaxysync` executable to add these files to a Galaxy Library, and then to a History

```
usage: galaxysync [-h] -address ADDRESS -api_key API_KEY -path PATH [-debug]

optional arguments:
  -h, --help        show this help message and exit
  -debug            toggles DEBUG-level logging output

required named arguments:
  -address ADDRESS  address of the local Galaxy instance
  -api_key API_KEY  a Galaxy admin API key
  -path PATH        the path to search for files to add
```

e.g.,
```
$ ./galaxysync -address "127.0.0.1" -api_key "<ADMIN KEY>" -path "/mnt/path"
```