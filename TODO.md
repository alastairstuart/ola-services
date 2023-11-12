
* Improve documentation of the services and protocol
* Turn the services into proper daemons that run in the background and controllable by init.d
* Both services should send their logger output to properly rotated log files.
* Create OpenWRT packages for the services to avoid the need for manual installation
* Run the services as non root users on OpenWRT to limit an potential damage
* Assess performance of python3 on real OpenWRT hardware - consider rewriting in Go or somthing else quick an maintainable instead
* Consider using virtual envs if staying with python, incase dependencies betwen services diverge 
* Things will break if we need to support another upload path - this should be handled more gracefully across the 2 services
* Uploaded logs are often with sub 4kb. The usual disk block size is 4kb meaning all files, even tiny 300 byte uploads, take up 4k on disk. It's inefficient to store them as individual files. The additional complexity of storing them in a SQLite database or similar would be a more efficient use of space, and probably also allow for more efficient garbage collection.
* Compression would also help with storage - using Gziped files or compressed representations in the above mentioned SQLite DB would help here.
* Things will break if we need to support another upload path - this should be handled more gracefully across the 2 services
* metrics_local: add configurability to the garbage collection 
* metrics_local: investigate more optimised bottle backends - e.g. FastWSGI
* hitchhiker_source: investigate improvements on grpclib - e.g. https://github.com/danielgtaylor/python-betterproto
* hitchhiker_source: make site id configurable
* hitchhiker_source: exit the service cleanly (there is a mess when using Ctrl-C)
