# Explainability UI for GNN models

## How to run this project
### Running the project
1. Clone the github repo
1. Install the python requirements: `pip install -r requirements.txt`
1. Change to `web` directory: `cd web`
1. Install the node modules: `npm install` (you need to install npm first)
1. Run the Vue app with command `npm run build`
1. Return to the main directory `cd ..`
1. Run the server with `python web_service.py` command. The server will listen to port 5000 on all networks by default.
The UI should be accessible from `http://localhost:5000`
### Running the frontend for development
1. Run the Vue app with command `npm run serve`. The frontend is accessible at `http://localhost:8080/`
and tries to communicate with backend at `http://localhost:5000`.


## How to add new experiments
There is an experiment template in the `experiments` folder which you can use as a starting point.
Copy `experiment.py` and modify it as necessary.