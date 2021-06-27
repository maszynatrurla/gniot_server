# Server for gnIoT and Kszynka

Simple http server written in python (webpy framework) for gnIoT project.

It accepts data temperature/humidity data from sensors (gniots) and stores them in the database.
It also has simple data visualization for user.

Another server handles data from weather station on the balcony (kszynka). It works in similar fashion
storing data in the database and displaying it for the user.


## Requirements

Frontend is dependent on chartjs library. Chartjs distribution package needs to be unpacked to chartjs/dist folder where server expects to find it.

Code is written for python3 and requires webpy and sqlite3 packages.


## Database

Project uses sqlite3 file-based database. You need to create database manually using schema from sql dir.

 * gniot.db - database for indoor temp/humidity sensors, single table 'sample' described in sql/gniot.db.sql file
 * kszynka.db - database for weather station, single table 'pogoda' described in sql/kszynka.db.sql file.
 
## Usage

This is very amateurish project written without much care, for specific use (collecting data from gniots and kszynka).

### gnIoT

Create gniot.db database, and start server from command line: python3 gniot.py [PORT]

PORT - optional specify http port to use.

gnIoT sensors must obviously be configured to connect to this server - modify their credentials.h file and put your server's IP and port there.


### Kszynka

Create kszynka.db database, and start server from command line: python3 kszynka.py [PORT]

PORT - optional specify http port to use.

Weather station must be configured with address and port to be able to sent data there.


### Frontend

Simple web pages that visualize recent/historical data.

For gnIoT sensor positions and room layout are hardcoded, so index.html file should be modified if it can be of any use to somebody else than me.

### Changing configuration of devices

gnIoTs and Kszynka can be reconfigured via server's response. To do that, create text file with name: konfigur_N (for gniot) or kszyfigur_N (for kszynka),
where N is ID of the device.

File needs to contain configuration in form of 

KEY VALUE

pairs, separated by whitespace. For configuration keys see source code of gniot/kszynka (service.c file).

This mechanism can also trigger OTA firmware upgrade of gniot.



