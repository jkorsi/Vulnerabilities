# Vulnerabilities  
For the University of Helsinki course Cyber Security Base 2024  
  
## Setup instructions:  
  
### On Windows   
cd to Vulnerabilities folder  
run: `python -m venv venv`  
run: `.\venv\Scripts\activate`  
run: `pip install -r requirements.txt`  
  
  
### On Mac & Linux  
cd to Vulnerabilities folder  
run: `python3 -m venv venv`  
run: `source venv/bin/activate`  
run: `pip install -r requirements.txt`  
  
## Run the server  
CD to base folder (that includes the manage.py)  
At first use, run: `python manage.py migrate`  
Afterwards, to run the server: `python manage.py runserver`  
