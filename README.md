# Shoppr
Barebones online marketplace.

# Installation Guide
This application requires Python3 and MySQL to run.

It is recommended to run the code of this repository within a virtual environment.
To create one, simply run:
```
python3 -m virtualenv venv
```

To activate it, run:
```
source venv/bin/activate
```

To install the required Python libraries, simply run:
```
pip3 install -r requirements.txt
```

Finally, to set up the database, run:
```
python3 setup.py
```

# Usage
To launch the application:
```
python3 app.py
```

It should run under `http://127.0.0.1:5000/`. The introduction page can be found here.

The application uses GraphQL, and has an interactive GraphiQL UI which can be found here: `http://127.0.0.1:5000/graphql`

Note that the functionalities have all been included as `mutations`. The GraphiQL docs describe sample usage for the various end-points.
