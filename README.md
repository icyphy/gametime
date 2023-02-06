 # gametime

## Docker
To build the docker file, run from home folder `docker build -t gametime -f docker/Dockerfile .`

To run the docker file, run `docker run -it gametime bash`

## Conda Environment
To conda environment for cross platform use, use `conda env export --from-history > conda_environment.yml`. This would export conda dependencies only explicitly installed with version number only if explicitly specified during installation. 