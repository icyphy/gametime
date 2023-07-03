


# gametime

## Docker
To build the docker file, run from home folder `docker build -t gametime -f docker/Dockerfile .`

To run the docker file, run `docker run -it gametime bash`

Using VS Code or Pycharm, you should be able to connect to your docker container interpreter and work from 
your host computer. 

## Conda Environment
To conda environment for cross platform use, use `conda env export --from-history > conda_environment.yml`.
This would export conda dependencies only explicitly installed with version number only if explicitly specified during installation. 

## Recommended Setup
Due to the fact that docker containers are large and cumbersome, the recommended setup is to use the docker container on a remote server. 
Then, it is possible to have IDE's like Pycharm of code editors like VS Code to connect remotely to the server, and then 
use the remote python interpreter in the docker container. 

### Pycharm
You would need Pycharm for this procedure. This procedure has only been tested on Pycharm Professional, which Berkeley 
students can access for free. First SSH into your remote server. Then, clone the repo 
`git clone git@github.com:icyphy/gametime.git`

Once the repo is cloned, setup Pycharm remote by clicking on the remote development menu on the left and then click "New Connection" 
button on the top right. Input your SSH information. This should allow pycharm to access your remote server. Once you are in 
the remote server, you should be able to point Pycharm to your newly cloned repo and open a remote session with Pycharm

To configure the interpreter, go to File->Settings->Project: Gametime->Python Interpreter. Add a new interpreter from
Docker. In the popup window select the folder `.` for context folder, and uncheck rebuilt each time for run at the bottom. 
Pycharm should be able to setup the interpreter and docker environment. Wait a few minutes, and you should have an interpreter
with packages such as PyPuLP available to it. 

As of 3/20/2023, Docker and Pycharm does not play well together, and many 
syntax highlighting features might be missing. To work around that, configure a local interpreter in the server
to gain syntax highlighting. Since we are not going to be using the interpreter to run our code, the exact environment
doesn't really matter, and you can add to it as you go. 

