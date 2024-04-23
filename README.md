# Manuel Blaser
Lab 6

### My project: https://manuelb-lab6.dynv6.net/


## Completion
In the beginning, I struggled with almost everything. I didn't understand how to use the syntax from flask with "@app.route", the methods and the required return statements in the functions.
Additionally, I didn't understand how to use the html files and how to access, pass variables and render them.
After some try end error I learnt how it works and after that I made quick progress.

Also, how to set up an SQL database caused many problems in the beginning. I didn't understand how to set up the .sql file and how to create, read and write into the database. Thus, I created a small example project, out of this project, on how to read, write and create a database. After doing that, the usage and handling of the database didn't cause problems anymore.

One big issue I had was the extraction of the IP. At the beginning, I didn't realize that I will always see the local host IP. Thus, I hardcoded a "fake IP" for testing purposes. After deploying the code to the oracle server, I faced the same issue again. With some additional lines in the nginx config file this issue could be solved.
Because of this issue, I didn't understand in the beginning why I never get GPS coordinates from the IP.

Accessing the weather data and classify the description with Google Gemini caused less problems than I thought.
As well the sorting and displaying the data was easier than expected. Pandas does a very good job there!

Setting up the oracle server was more challenging. At first, I had problems with installing Miniconda. The version shown in the video and in the slides didn't work. Somehow, I used another OS on my server than shown. After downloading Miniconda for Linux it worked. Also, installing Nginx, open the reqired ports in the firewall and configure everything was annoying. Though, I learnt a lot. After some tinkering around with the server I start to understand better what's going on. Then, setting up the conda environment with the required libraries wasn't hard anymore.

During deploying and troubleshooting of the server, I also learnt a lot about the handling with git!

## Instruction video
[Link to the video](./Instruction_video/video1884365989.mp4)

##

I worked alone for this project and developed the cody by myself.
