# Planeación de Semáforos

A project presented at college and received recognition for it.
## Description of the Project

It is an evolutionary algorithm that, based on velocity, directions, length, and security rules, determines the best places to put traffic lights. This is based on a function that analyzes the data of each street, the rules, and whether there is already a traffic light in the area, to either give or remove points from the result. The street with the highest score is selected, offering a visualization on the map of the city to indicate where the traffic lights should be placed.
## How to use
### Clone the project
``` bash
git clone git@github.com:jvasquezt2004/Planeacion-de-semaforos.git
```
### Install the requirements from requirements.txt
``` bash
pip install -r requirements.txt
```
### Run the main.py file
``` bash
python main.py
```
### Take into consideration that this is a very heavy algorithm, so the results may take a few minutes to an hour, depending on your hardware.
If you want to change the map, simply change the place in the string, and the algorithm will work the same.
