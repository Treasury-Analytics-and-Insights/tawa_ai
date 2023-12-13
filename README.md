# Introduction 
This is a prototype ChatBot for interpreting TAWA microsimulation model results.

# Installation process
This project is setup to use pipenv for managing dependencies.  This way a python
virtual environment is created specifically for this project.  To install pipenv
on your system, follow the instructions here: https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv

Once pipenv is installed, you can install the dependencies for this project by running:
```pipenv install```
```
from the root directory of this project.  This will create a virtual environment
and install all the dependencies.  One of the dependencies is the aipy package
which currently is installed from source.  You'll need to clone this from DevOps
and modify the Pipfile to point to the location of the aipy work directory.
```

# Running the ChatBot

To run the ChatBot, you'll need to activate the virtual environment created by pipenv.
You can do this by running:
```pipenv shell```

Then you can start the ChatBot by running:
```panel serve tawa_chatbot.py```

This will start the ChatBot on port 5006.  You can access it by going to:
```http://localhost:5006/tawa_chatbot```

The ChatBot takes two inputs:
1. An excel file containing output from a TAWA standard TAR (as cleared from the IDI).
2. A yaml file that contains descriptions of the reform scenarios contained in the output file.
See the files in the input directory for examples of these files.

Before asking the chatbot any questions, you'll need to disable your http proxy.  This is a limitation of the openai api.
