WIP mu.semte.ch service to compute frequent item sets.

# Building the image
Build the docker image using
```
dr build -t freqs .
```
# Running
For debugging, you can start the container on its own using the command
```
dr run --name freqs --link virtuoso:database -p 80:80 --rm -it freqs
```
make sure to link it to the database you have running.

You can add it into a docker-compose.yml file like this:
```
	freqs:
		ports:
			- 80:80
		links:
			- virtuoso:database
```

# TODO
- better detection of whether itemset is already found in maximal itemset detection
