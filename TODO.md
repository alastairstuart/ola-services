
* Create proper init.d files for both services so OpenWRT can manage them as it does other daemons
* Assess performance of python3 on OpenWRT - consider rewriting in Go instead.
* Things will break if we need to support another upload path - this should be handled more gracefully across the 2 services
* Uploaded logs are often with sub 4kb. The usual disk block size is 4kb meaning all files, even tiny 300 byte uploads, take up 4k on disk. It's inefficient to store them as individual files. The additional complexity of storing them in a SQLite database or similar would be a more efficient use of space, and probably also allow for more efficient garbage collection.
* Compression would also help with storage - using Gziped files or compressed representations in the above mentioned SQLite DB would help here.
* Things will break if we need to support another upload path - this should be handled more gracefully across the 2 services
* metrics_local: configurably disable the garbage collection
* metrics_local: investigate more optimised bottle backends - e.g. FastWSGI
* hitchhiker_source: investigate improvements on grpclib - e.g. https://github.com/danielgtaylor/python-betterproto
