Basic mu.semte.ch service to compute frequent item sets.

# Building the image
Build the docker image using
```
dr build -t freqs .
```
# Running
Run the container like this:

```
dr run --name freqs --link virtuoso:database -p 80:80 --rm -e LOG_LEVEL=info -e FP_WORKERS=10 -it freqs
```

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

# Using the webservice
The webservice offers access to a set of predefined mining configurations. The configurations can be set in the config.yaml file, located in /app/config.yaml

this file has the followoging syntax:

```
skills:
  transactions: 'select ?basket GROUP_CONCAT(DISTINCT ?skill; separator=",") AS ?items where {
  ?basket a <http://data.europa.eu/esco/model#Occupation> .
  ?rel a <http://data.europa.eu/esco/model#Relationship>.
  ?rel <http://data.europa.eu/esco/model#isRelationshipFor> ?basket.
  ?rel <http://data.europa.eu/esco/model#refersConcept> ?skill.
} group by ?basket'
```
Here ```skills``` is the name of a configuration. The configuration has only one setting, ```transactions```. This holds a sparql query that fetches a list of transactions, identified by some id in the ```?basket``` variable, with a list of items in the ```?items``` variable.

You can start mining a set of transactions by doing

```
GET <<service-location>>/mine-fp/example?support=0.2
```

This will start a run of the service. Get the status (or final result of a run by doing

```
GET localhost/mining-state/<<id-returned-by-the-previous-get>>
```

Note that when this call returns any data, the data will be removed from memory afterward.
