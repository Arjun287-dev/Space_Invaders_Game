
SPACE INVADERS

The "Space Invaders" game, developed using Pygame and MySQL, is an immersive arcade-style game
designed with a touch of futuristic style to provide players with an engaging and competitive experience. This project takes inspiration from the classic space shooter genre, allowing players to test their reflexes and strategy as they combat waves of
alien invaders. The game offers a unique opportunity for players to compete with friends, with the goal of
achieving the highest score and securing their position on the leaderboard.

The following are the steps to setup and run the game:

Step 1 - Libraries that is required to run this project are(Using the terminal):

    1. pip install pygame.

    2. pip install mysql.connector.

    3. pip install hashlib. (Only if you are using python version older than 2.4)

Step 2 - Setting up database for the game:

    step 1 - Download and install the MySQL version 9.1.

    step 2 - setup your environment accordingly.

    step 3 - Creating a new database and name it as "game_db" using the following code:

    Create database game_db;

    step 4 - Creating table for storing the data of the game using the following code:

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_logged_in INTEGER DEFAULT 0,
        highest_score INTEGER DEFAULT 0
    );


Step 3 - To run the Game-

    step 1 - Extract the zip file

    step 2 - Open space-invaders-game folder

    step 3 - Open the Space-Invaders.py 

    step 4 - Change all the path in the Space-Invaders.py to your own path

    step 5 - Connect the database to the Space-Invaders.py by changing the database credentials accordingly in the def connect_to_database()

    step 6 - Run the Space-Invaders.py

Specs-

Processor: Intel Core i5 (7th Gen) or above, or AMD Ryzen 5
RAM: 8 GB or more
Storage: 256 GB SSD for faster read/write operations
Graphics: Dedicated GPU
Operating System: Windows 11, macOS 11 (Big Sur), or Linux Ubuntu 20.04 LTS
Display: Full HD (1920 x 1080) or higher
Network: High-speed internet connection

Contact Me-

If you find any problem in the game please contact me through my email arjunarundiyar28@gmail.com which will help me improve the game further more

Thank you for playing Space Invaders. Have a great day.