# Explainability UI for GNN models

## How to run this project
### Running the backend server
1. Clone the github repo
1. Install the python requirements: `pip install -r requirements.txt`
1. Run the server with `python web_service.py` command. The server will listen to port 5000 on all networks by default
### Running the frontend for development
1. Change directory to the `web` folder.
1. Install the node modules: `npm install`
1. Run the Vue app with command `npm run serve`. The frontend is accessible at `http://localhost:8080/`


## How to add new experiments
There is an experiment template in the `experiments` folder which you can use as a starting point.
Copy `experiment.py.template` and modify it as necessary.