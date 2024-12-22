import pygame
import random
import sys
from pygame import mixer
from button import Button  # Ensure this Button class supports text-only buttons
import mysql.connector
import time 
from hashlib import sha256
import hashlib

pygame.init()

# window DIMENSIONS
global WIDTH,HEIGHT
WIDTH, HEIGHT = 800, 600

FULLwindow_WIDTH, FULLwindow_HEIGHT = 1360, 768
window = pygame.display.set_mode((WIDTH, HEIGHT))
fullwindow = False

# ICON AND HEADING
pygame.display.set_caption("SPACE INVADERS")
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)

# BACKGROUND
background_8x6 = pygame.image.load('background 8x6.png')
background_13x7 = pygame.image.load('background 13x7.png')
background_photo = background_8x6
BLACK=(0,0,0)
GREY=(192,192,192)
login_signup_bg_8x6=pygame.image.load('INTRO_BG_8x6.png')
login_signup_bg_17x7=pygame.image.load('INTRO_BG_13x7.png')
login_signup_bg=login_signup_bg_8x6

# GLOBAL VARIABLES
is_muted = False
logged_in_username = None
db = None
cursor = None

# Define file paths
game_over_path = 'game-over.mp3'
start_music_path = 'game-start.mp3'
BG_music_path = 'background.wav'
bullet_sound_path = 'laser.wav'
explosion_sound_path = 'explosion.wav'
select_sound_path = 'select_sound.mp3'
boss_music_path='boss_spawn.mp3'

# Load background music and other long tracks
def play_BG_music():
    mixer.music.load(BG_music_path)
    mixer.music.play(-1)

def play_ideal_music():
    mixer.music.load('space_music.mp3')  # Load the music file
    mixer.music.play(-1)  # Play the music indefinitely

# Load sound effects
game_over_music=mixer.Sound(game_over_path)
start_music = mixer.Sound(start_music_path)
bullet_sound = mixer.Sound(bullet_sound_path)
explosion_sound = mixer.Sound(explosion_sound_path)
select_sound = mixer.Sound(select_sound_path)
boss_music=mixer.Sound(boss_music_path)

# Example functions for playing sound effects
def play_bullet_sound():
    bullet_sound.play()

def play_explosion_sound():
    explosion_sound.play()

def play_select_sound():
    select_sound.play()

def play_boss_music():
    boss_music.play()

#Player sprite sheet 
sprite_sheet=pygame.image.load('starship_sprite_sheet.png').convert_alpha()

#Number of steps (frame) of player
Player_animation_steps=[9]
Player_size_width=187
Player_size_height=220
Player_data=[Player_size_width,Player_size_height]

#Number of steps (frame) of bullet
bullet_animation_steps=[3,4]
bullet_size_width=123
bullet_size_height=130
bullet_data=[bullet_size_width,bullet_size_height]

# Load enemy images
enemy_images = [
    pygame.transform.scale(pygame.image.load(f'ES-{i}.png'), (140, 145)) 
    for i in range(1, 13)
]
# Load enemy images
boss_images = [
    pygame.transform.scale(pygame.image.load(f'ES-{i}.png'), (140, 145)) 
    for i in range(14,22)
]

bullet_sprite_sheet=pygame.image.load('P-bullet.png')
pygame.transform.scale((bullet_sprite_sheet),(10,20))

boss_bullet_img=pygame.image.load('Boss_bullet.png')
pygame.transform.scale((boss_bullet_img),(60,56))

# PLAYER CLASS
class Player:
    def __init__(self, x, y, animation_steps):
        try:
            # Load the sprite sheet (update the path if needed)
            self.sprite_sheet = pygame.image.load('starship_sprite_sheet.png').convert_alpha()
        except pygame.error as e:
            self.sprite_sheet = None

        # Check if sprite sheet loaded successfully
        if self.sprite_sheet is None:
            raise ValueError("Sprite sheet not loaded. Cannot create player.")

        self.animation_steps = animation_steps
        self.size_width = 153  # Updated frame width based on sprite sheet size
        self.size_height = 180  # As per the sprite sheet height
        self.action = 0  # 0=idle
        self.frame_index = 0
        self.x_vel = 0
        self.y_vel = 0
        self.x = x
        self.y = y
        self.health = 100
        self.update_time = pygame.time.get_ticks()
        self.animation_list = self.load_images(self.sprite_sheet, animation_steps)

        if len(self.animation_list) > 0:
            self.image = self.animation_list[self.action][self.frame_index]
        else:
            self.image = None

    def update(self):
        animation_cooldown = 200
        if len(self.animation_list) > self.action and len(self.animation_list[self.action]) > self.frame_index:
            self.image = self.animation_list[self.action][self.frame_index]

        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0  # Loop back to the first frame
            self.update_time = pygame.time.get_ticks()

    def draw(self, window, invincible):
        if self.image is None:
            return  # Skip drawing if the image is not initialized

        # Create a copy of the player's image
        player_image = self.image.copy()
        
        # If the player is invincible, set the opacity to half
        if invincible:
            player_image.set_alpha(128)  # Set alpha to 128 for 50% opacity

        window.blit(player_image, (self.x, self.y))  # Draw the player image

    def get_width(self):
        if self.image:
            return self.image.get_width()
        return 0

    def get_height(self):
        if self.image:
            return self.image.get_height()
        return 0

    def load_images(self, sprite_sheet, animation_steps):
        if sprite_sheet is None:
            return []

        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(pygame.Rect(
                    x * self.size_width,
                    y * self.size_height,
                    self.size_width,
                    self.size_height
                ))
                temp_img_list.append(temp_img)
            animation_list.append(temp_img_list)
        return animation_list
    
# ENEMY CLASS
class Enemy:
    def __init__(self, x, y, type_idx):
        # Ensure enemy images are loaded properly
        if type_idx >= len(enemy_images) or not enemy_images:
            raise ValueError("Invalid enemy type index or no images loaded.")

        self.ship_img = enemy_images[type_idx]  # Assign the enemy image based on type index
        self.speed = random.uniform(1.0, 4.0)  # Random speed between 0.5 and 2.0
        self.x = x
        self.y = y
        self.health = 100
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def draw(self, window):
        if self.ship_img is None:
            return  # Skip drawing if the image is not initialized
        
        # Draw the enemy on the game window
        window.blit(self.ship_img, (self.x, self.y))

    def get_width(self):
        # Return the width of the enemy image
        return self.ship_img.get_width() if self.ship_img else 0

    def get_height(self):
        # Return the height of the enemy image
        return self.ship_img.get_height() if self.ship_img else 0

    def move(self, vel):
        # Move the enemy downwards at a rate proportional to its speed
        self.y += vel * self.speed

    def update_speed(self):
        # Randomly increase or decrease speed slightly
        self.speed += random.uniform(-0.2, 0.2)
        # Keep speed within the defined limits (between 0.8 and 2.0)
        self.speed = max(0.8, min(self.speed, 2.0))

#BOSS CLASS        
class Boss:
    def __init__(self, x, y,type_idx):
        # Ensure enemy images are loaded properly
        if type_idx >= len(boss_images) or not boss_images:
            raise ValueError("Invalid enemy type index or no images loaded.")

        self.ship_img = boss_images[type_idx]  # Assign the boss image based on type index
        self.bullet_img = boss_bullet_img
        self.health = 5
        self.x_vel = 3
        self.x = x
        self.y = y
        self.direction = 1
        self.last_shot = pygame.time.get_ticks()
        self.shoot_interval = 800  # Boss shoots every second

    def get_width(self):
        return self.ship_img.get_width() if self.ship_img else 0 

    def get_height(self):
        return self.ship_img.get_height() if self.ship_img else 0

    def move(self):
        self.x += self.x_vel * self.direction
        
        # Correct the position if it goes out of bounds before changing direction
        if self.x <= 50:
            self.x = 50
            self.direction *= -1
        elif self.x >= (WIDTH - 50) - self.get_width():
            self.x = (WIDTH - 50) - self.get_width()
            self.direction *= -1

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_interval:
            boss_bullets.append({"x": self.x + self.get_width() // 2, "y": self.y + self.get_height(), "state": "fire"})
            self.last_shot = now

    def draw(self, window):
        health_bar = pygame.Rect(self.x, self.y - 10, self.get_width() * (self.health / 5), 5)
        pygame.draw.rect(window, (255, 0, 0), health_bar)
        window.blit(self.ship_img, (self.x, self.y))

    def update_speed(self):
        # Randomly increase or decrease speed slightly
        self.speed += random.uniform(-0.2, 0.2)
        # Keep speed within the defined limits (between 0.8 and 2.0)
        self.speed = max(1, min(self.speed, 2.5))

#BULLET CLASS
class Bullet:
    def __init__(self, x, y, sprite_sheet, animation_steps):
        self.x = x
        self.y = y
        self.sprite_sheet = sprite_sheet
        self.size_width = 41
        self.size_height = 74
        self.action = 0  # 0 = idle
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.animation_list = self.load_images(self.sprite_sheet, animation_steps)
        
        if self.animation_list:
            self.image = self.animation_list[self.action][self.frame_index]

        self.is_collided = False  # To track if bullet has collided

    def update(self):
        animation_cooldown = 100
        
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0  # Loop back to the start

            self.image = self.animation_list[self.action][self.frame_index]  # Update image
            self.update_time = pygame.time.get_ticks()  # Reset the timer

        if not self.is_collided:
            self.y -= 15  # Adjust bullet speed

    def draw(self, window):
        if self.image:
            window.blit(self.image, (self.x, self.y))

    def get_width(self):
        return self.image.get_width() if self.image else 0

    def get_height(self):
        return self.image.get_height() if self.image else 0

    def load_images(self, sprite_sheet, animation_steps):
        animation_list = []
        sheet_width, sheet_height = sprite_sheet.get_size()  # Get sprite sheet dimensions

        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                # Calculate the rectangle dimensions to extract a frame from the sprite sheet
                rect = pygame.Rect(
                    x * self.size_width,  # X position
                    y * self.size_height,  # Y position
                    self.size_width,       # Width of each frame
                    self.size_height       # Height of each frame
                )

                # Ensure the rect does not exceed sprite sheet bounds
                if rect.right <= sheet_width and rect.bottom <= sheet_height:
                    temp_img = sprite_sheet.subsurface(rect)
                    temp_img_list.append(temp_img)
            animation_list.append(temp_img_list)

        return animation_list

# Connect to the database
def connect_to_database():
    global db, cursor
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='game_db'
    )
    cursor = db.cursor()

# Function to check if any user is logged in based on the 'is_logged_in' flag
def check_logged_in_user():
    ensure_connection()  # Ensure the database connection is active

    query = "SELECT username FROM users WHERE is_logged_in = 1 LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None  # Return the username if a logged-in user is found
    return None

def ensure_connection():
    global db, cursor
        # Ensure that connection is open
    if db is None or db.is_connected() == False:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arjun@287',
            database='game_db'
        )
        cursor = db.cursor()

# Check if any user is already logged in by querying the DB
def get_logged_in_user():
    ensure_connection()  # Ensure the connection is active
    query = "SELECT username FROM users WHERE is_logged_in = 1"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None

def authenticate_user(username, password):
    # Hash the password entered by the user
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Query to check if a user exists with the given username and hashed password
    query = "SELECT username FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, hashed_password))
    
    user = cursor.fetchone()
    return user  # Returns the user if found, otherwise returns None

# Login function
def login(username, password):
    ensure_connection()  # Ensure the connection is active
    hashed_password = sha256(password.encode()).hexdigest()  # Hash the password
    cursor.execute("SELECT username FROM users WHERE username=%s AND password=%s", (username, hashed_password))
    user = cursor.fetchone()
    
    if user:
        set_login_status(username, True)  # Mark user as logged in
        return True
    return False

# Signup function
def signup(username, password):
    ensure_connection()  # Ensure the connection is active
    hashed_password = sha256(password.encode()).hexdigest()  # Hash the password
    query = "INSERT INTO users (username, password, is_logged_in) VALUES (%s, %s, %s)"
    
    cursor.execute(query, (username, hashed_password, 1))  # Automatically set logged in after signup
    db.commit()

def set_user_logged_in(username):
    ensure_connection()  # Ensure the connection is open before proceeding

    # Update query to set is_logged_in to 1 (for login)
    query = "UPDATE users SET is_logged_in = %s WHERE username = %s"
    cursor.execute(query, (1, username))  # Set is_logged_in to 1
    db.commit()

def set_login_status(username):
    ensure_connection()  # Ensure the connection is open before proceeding

        # Update query to set is_logged_in to 0 (for logout)
    query = "UPDATE users SET is_logged_in = %s WHERE username = %s"
    cursor.execute(query, (0, username))  # Set is_logged_in to 0
    db.commit()

    if cursor:
        cursor.close()  # Close the cursor after logout operation
    if db.is_connected():
        db.close()  # Close the database connection after logout operation

def check_username_exists(username):

    # Query the database to check if the username already exists
    cursor = db.cursor()  # Replace 'connection' with your actual database connection object
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    count = cursor.fetchone()[0]
    cursor.close()
    return count == 0  # Return True if username is available (count is 0)
# function to get the highest score from the database
def fetch_highest_score(username):
    ensure_connection()  # Ensure connection is established

    query = "SELECT highest_score FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    return result[0] if result else 0  # Return 0 if no score is found

def save_user_to_database(username, password):
    # Hash the password for secure storage
    hashed_password = sha256(password.encode()).hexdigest()  # Using SHA-256 hashing

            # SQL query to insert a new user
    query = "INSERT INTO users (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, hashed_password))
        
        # Commit the transaction
    db.commit()

def update_highest_score(username, new_score):
    cursor.execute("UPDATE users SET highest_score = %s WHERE username = %s", (new_score, username))
    db.commit()  # Don't forget to commit the transaction to save the changes

def get_user_input(prompt_text):
    user_input = ""
    run = True
    while run:
        window.blit(login_signup_bg, (0, 0))
        prompt = get_font(40).render(prompt_text, True, (BLACK))
        window.blit(prompt, (WIDTH * 0.2, HEIGHT * 0.4))

        # Display the current user input
        user_input_display = get_font(30).render(user_input, True, (BLACK))
        window.blit(user_input_display, (WIDTH * 0.2, HEIGHT * 0.5))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Capture typed characters
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Press Enter to confirm input
                    run = False
                elif event.key == pygame.K_BACKSPACE:  # Handle backspace
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode  # Add typed character to input

    return user_input

def close_database():
    global cursor, db
    if cursor is not None:
        cursor.close()
    if db is not None and db.is_connected():
        db.close()

def logout_user(username):
    try:
        ensure_connection()

        # Update query to set is_logged_in to 0 (for logout)
        query = "UPDATE users SET is_logged_in = %s WHERE username = %s"
        cursor.execute(query, (0, username))  # Setting is_logged_in to 0
        db.commit()
    finally:
        if cursor:
            cursor.close()
        if db.is_connected():
            db.close()

def display_message(message, color=(255, 0, 0), duration=2, show_back=False):
    """Function to display a message on the screen and handle back button."""

    back_button = None
    run_message_display = True
    
    start_time = time.time()  # Track the start time
    while run_message_display:
        
        window.blit(login_signup_bg, (0, 0))
        # Render and display the message
        message_surface = get_font(40).render(message, True, color)
        window.blit(message_surface, (WIDTH * 0.5 - message_surface.get_width() // 2, HEIGHT * 0.2))

        # If the back button should be shown (for errors)
        if show_back:
            back_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.5), text_input="BACK", font=get_font(40), base_color=(BLACK), hovering_color=(GREY))
            back_button.changeColor(pygame.mouse.get_pos())
            back_button.update(window)

        pygame.display.update()

        # Check for events (like closing the window or clicking the back button)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if show_back and event.type == pygame.MOUSEBUTTONDOWN and back_button and back_button.checkForInput(event.pos):
                return "back"  # Return "back" when back button is clicked

        # If no back button is shown, wait for the specified duration and exit
        if not show_back and time.time() - start_time >= duration:
            run_message_display = False

def login(username="", password=""):
    run = True

    while run:
        window.blit(login_signup_bg, (0, 0))  # Render the login background

        # Render username and password fields
        username_input = login_font(30).render(f"Username: {username}", True, (BLACK))
        password_input = login_font(30).render(f"Password: {password}", True, (BLACK))  # Mask the password

        window.blit(username_input, (WIDTH * 0.5 - username_input.get_width() // 2, HEIGHT * 0.4))
        window.blit(password_input, (WIDTH * 0.5 - password_input.get_width() // 2, HEIGHT * 0.5))

        # Confirm button for login
        confirm_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), text_input="CONFIRM", font=get_font(40),
                                base_color=(BLACK), hovering_color=(GREY))
        confirm_button.changeColor(pygame.mouse.get_pos())
        confirm_button.update(window)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle username input
            if event.type == pygame.KEYDOWN:
                # Fullscreen toggle with Ctrl+Shift+F
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    toggle_fullwindow()

                # Check if Enter key is pressed
                if event.key == pygame.K_RETURN:
                    user = authenticate_user(username, password)  # Use the username and password for authentication

                    if user:  # If login is successful
                        logged_in_username = user[0]  # Assuming the first element in 'user' is the username
                        display_message("Login successful!", color=(0, 255, 0), duration=2)  # Show success message in green
                        run = False

                        # Fetch highest score and proceed to the main game
                        set_user_logged_in(username)
                        highest_score = fetch_highest_score(logged_in_username)
                        main(logged_in_username)  # Pass the username and score to the main game
                    else:
                        # If login fails, show an error message
                        action = display_message("Invalid credentials!", color=(255, 0, 0), duration=2, show_back=True)  # Red color for error
                        if action == "back":
                            login_signup()  # Return to the login/signup screen
                            run = False  # Exit current loop

            # Handle mouse clicks for the confirm button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.checkForInput(event.pos):
                    # Check user credentials using the correct login function
                    user = authenticate_user(username, password)  # Use the username and password for authentication
                    
                    if user:  # If login is successful
                        logged_in_username = user[0]  # Assuming the first element in 'user' is the username
                        display_message("Login successful!", color=(0, 255, 0), duration=2)  # Show success message in green
                        run = False
                        
                        # Fetch highest score and proceed to the main game
                        set_user_logged_in(username)
                        highest_score = fetch_highest_score(logged_in_username)
                        main(logged_in_username)  # Pass the username and score to the main game
                    else:
                        # If login fails, show an error message
                        action = display_message("Invalid credentials!", color=(255, 0, 0), duration=2, show_back=True)  # Red color for error
                        if action == "back":
                            login_signup()  # Return to the login/signup screen
                            run = False  # Exit current loop

def signup(username="", password=""):

    run = True
    
    while run:
        window.blit(login_signup_bg, (0, 0))      

        # Display the current username and password on the screen
        username_input = login_font(30).render(f"Username: {username}", True, (BLACK))
        password_input = login_font(30).render(f"Password: {password}", True, (BLACK))  # Mask the password

        # Render the username and password fields at the designated positions
        window.blit(username_input, (WIDTH * 0.5 - username_input.get_width() // 2, HEIGHT * 0.4))
        window.blit(password_input, (WIDTH * 0.5 - password_input.get_width() // 2, HEIGHT * 0.5))

        # Display the Confirm button only if username and password are not empty
        confirm_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), text_input="CONFIRM", font=get_font(40), base_color=(BLACK), hovering_color=(GREY))
        confirm_button.changeColor(pygame.mouse.get_pos())
        confirm_button.update(window)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle username input
            if event.type == pygame.KEYDOWN:
                # Fullscreen toggle with Ctrl+Shift+F
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    toggle_fullwindow()

                # Check if Enter key is pressed
                if event.key == pygame.K_RETURN:
                    if check_username_exists(username):
                        # Save the user to the database
                        save_user_to_database(username, password)
                        display_message("Signup successful!", color=(0, 255, 0), duration=2)  # Green color for success
                        run = False
                        main(username)  # Proceed to the game
                    else:
                        # Show "Username already taken" message
                        action = display_message("Username already taken!", color=(255, 0, 0), duration=2, show_back=True)
                        if action == "back":
                            login_signup()  # Return to the login/signup screen
                            run = False  # Exit current loop

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Confirm button clicked
                if confirm_button.checkForInput(event.pos):
                    # Check if username is available before saving
                    if check_username_exists(username):
                        # Save the user to the database
                        save_user_to_database(username, password)
                        display_message("Signup successful!", color=(0, 255, 0), duration=2)  # Green color for success
                        run = False
                        main(username)  # Proceed to the game
                    else:
                        # Show "Username already taken" message
                        action = display_message("Username already taken!", color=(255, 0, 0), duration=2, show_back=True)
                        if action == "back":
                            login_signup()  # Return to the login/signup screen
                            run = False  # Exit current loop

def check_and_update_highest_score(username, current_score, highest_score):
    if current_score > highest_score:
        update_highest_score(username, current_score)
        return current_score  # Return the new highest score
    return highest_score  # No update, return the old highest score

def fire_bullet(x, y):
    # Initialize a new bullet when the space bar is pressed
    bullet = Bullet(x, y, bullet_sprite_sheet, bullet_animation_steps)
    bullets.append(bullet)

def get_font(size):
    return pygame.font.Font('ethnocentric rg.otf', size)

def login_font(size):
    return pygame.font.Font('Oregon.ttf', size)

# COLLISION
def isCollision(rect1, rect2):
    return rect1.colliderect(rect2)

# TOGGLE FULLwindow
def toggle_fullwindow():
    global fullwindow, WIDTH, HEIGHT, window, background_13x7, background_8x6, background_photo,login_signup_bg
    fullwindow = not fullwindow
    if fullwindow:
        background_photo = background_13x7
        login_signup_bg=login_signup_bg_17x7
        WIDTH, HEIGHT = FULLwindow_WIDTH, FULLwindow_HEIGHT
        window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        WIDTH, HEIGHT = 800, 600
        background_photo = background_8x6
        window = pygame.display.set_mode((WIDTH, HEIGHT))

def toggle_mute():
    global is_muted
    is_muted = not is_muted
    volume_level = 0 if is_muted else 0.5  # Set volume to 0 if muted, else 1

    mixer.music.set_volume(volume_level)  # For background music
    start_music.set_volume(volume_level)  # For start music
    bullet_sound.set_volume(volume_level)  # For bullet sound
    explosion_sound.set_volume(volume_level)  # For explosion sound
    select_sound.set_volume(volume_level)  # For select sound

def intro():
    play_ideal_music()
    while True:
        window.blit(login_signup_bg, (0, 0))

        intro_title_text = get_font(60).render("SPACE INVADERS", True, (BLACK))
        intro_title_rect = intro_title_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.3))
        window.blit(intro_title_text, intro_title_rect)

        mess_text = get_font(20).render("Press ENTER To Start.", True, (BLACK))
        mess_rect = mess_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.8))
        window.blit(mess_text, mess_rect)

        # Step 1: Connect to the database
        connect_to_database()

        # Step 2: Check if any user is already logged in
        logged_in_user = get_logged_in_user()

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_database()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    toggle_fullwindow()
                if event.key == pygame.K_RETURN:  # Direct comparison instead of 'in'
                    connect_to_database()
                    try:
                        if logged_in_user:
                            main(logged_in_user)  # Pass the logged-in user to the main game function
                        else:
                            login_signup()  # No user logged in, so take them to login/signup screen
                    
                    finally:
                        # Step 4: Close the database connection
                        close_database()

# PAUSE GAME
def pause_game(username):
    global bullets,boss_bullets,enemies,score_value
    highest_score = fetch_highest_score(username)
    paused = True
    transparency = 128  # 0 is fully transparent, 255 is fully opaque
    overlay = pygame.Surface((WIDTH,HEIGHT))
    play_ideal_music()
    overlay.set_alpha(transparency)
    overlay.fill((0, 0, 0))

    while paused:
        window.blit(background_photo, (0, 0))
        window.blit(overlay, (0, 0))  # Blit the transparent overlay

        pause_text = get_font(70).render("PAUSED", True, (BLACK))
        pause_rect = pause_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.3))
        window.blit(pause_text, pause_rect)

        # Add buttons for unpause, Setting, and exit
        resume_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.5), text_input="RESUME", font=get_font(30), base_color=(BLACK), hovering_color=(GREY))
        Restart_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.6), text_input="RESTART",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        Setting_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), text_input="SETTINGS", font=get_font(30), base_color=(BLACK), hovering_color=(GREY))
        exit_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.8), text_input="EXIT", font=get_font(30), base_color=(BLACK), hovering_color=(GREY))

        resume_button.changeColor(pygame.mouse.get_pos())
        resume_button.update(window)
        Restart_button.changeColor(pygame.mouse.get_pos())
        Restart_button.update(window)
        Setting_button.changeColor(pygame.mouse.get_pos())
        Setting_button.update(window)
        exit_button.changeColor(pygame.mouse.get_pos())
        exit_button.update(window)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_button.checkForInput(event.pos):
                    paused = False
                if Restart_button.checkForInput(event.pos):
                    bullets = []
                    boss_bullets = []
                    enemies = []
                    score_value = 0
                    play_BG_music()
                    gameplay(username, highest_score)  # Pass updated highest score
                elif Setting_button.checkForInput(event.pos):
                    SettingP_menu(username)
                elif exit_button.checkForInput(event.pos):
                    set_user_logged_in(username)
                    main(username)
        pygame.display.update()

def SettingP_menu(username):
    global in_optionP
    in_optionP=True
    play_ideal_music()
    overlay=pygame.Surface((WIDTH,HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((BLACK))    

    def Controls(): 
        in_Controls=True
        overlay=pygame.Surface((WIDTH,HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((BLACK))    

        while in_Controls:
                    window.blit(background_photo,(0,0))
                    window.blit(overlay,(0,0))
                    fullwindow_text=get_font(15).render("Ctrl + Shift + F : Toggle Fullwindow",True,(255, 255, 255))
                    fullwindow_rect=fullwindow_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.2))
                    window.blit(fullwindow_text,fullwindow_rect)
                    Exit_fullwindow_text=get_font(15).render("Esc : To Pause Game",True,(255, 255, 255))
                    Exit_fullwindow_rect=Exit_fullwindow_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.3))
                    window.blit(Exit_fullwindow_text,Exit_fullwindow_rect)
                    movementright_text=get_font(15).render("D, Right Arrow : To Move Right",True,(255, 255, 255))
                    movementright_rect=movementright_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.4))
                    window.blit(movementright_text,movementright_rect)
                    movementleft_text=get_font(15).render("A, Left Arrow : To Move Left",True,(255, 255, 255))
                    movementleft_rect=movementleft_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.5))
                    window.blit(movementleft_text,movementleft_rect)
                    movementup_text=get_font(15).render("W, Up Arrow : To Move Upward",True,(255, 255, 255))
                    movementup_rect=movementup_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.6))
                    window.blit(movementup_text,movementup_rect)
                    movementdown_text=get_font(15).render("S, Down Arrow : Player Movement",True,(255, 255, 255))
                    movementdown_rect=movementdown_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.7))
                    window.blit(movementdown_text,movementdown_rect)
                    Fire_text=get_font(15).render("Space : To Fire Bullet",True,(255, 255, 255))
                    Fire_rect=Fire_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.8))
                    window.blit(Fire_text,Fire_rect)
                    Exitc_text = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.9), text_input="EXIT", font=get_font(25), base_color=(BLACK), hovering_color=(GREY))
                    Exitc_text.changeColor(pygame.mouse.get_pos())
                    Exitc_text.update(window)

                    for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()  
                            if event.type==pygame.MOUSEBUTTONDOWN:
                                if Exitc_text.checkForInput(pygame.mouse.get_pos()):
                                    select_sound.play()
                                    in_Controls=False
                                    SettingP_menu(username)
                    pygame.display.update()

    while in_optionP:
        window.blit(background_photo,(0,0))
        window.blit(overlay,(0,0))

        Setting_text= get_font(70).render("SETTINGS",True,(BLACK))
        Setting_rect = Setting_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.3))
        window.blit(Setting_text,Setting_rect)
        

        #MUTE BUTTON
        mute_text="UNMUTE" if is_muted else "MUTE"
        mute_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.5), text_input=mute_text,font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        controls_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.6), text_input="CONTROLS",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        back_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.7), text_input="BACK",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        
        
        mute_button.changeColor(pygame.mouse.get_pos())
        mute_button.update(window)
        controls_button.changeColor(pygame.mouse.get_pos())
        controls_button.update(window)
        back_button.changeColor(pygame.mouse.get_pos())
        back_button.update(window)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if mute_button.checkForInput(pygame.mouse.get_pos()):
                    select_sound.play()
                    toggle_mute()
                if controls_button.checkForInput(pygame.mouse.get_pos()):
                    select_sound.play()
                    Controls()
                if back_button.checkForInput(pygame.mouse.get_pos()):
                    select_sound.play()
                    in_optionP=False
                    pause_game(username)
        pygame.display.update()

def Setting_menu(username):
    global in_option
    in_option=True
    play_ideal_music()
    overlay=pygame.Surface((WIDTH,HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0,0,0))    

    def Controls():
        in_Controls=True
        overlay=pygame.Surface((WIDTH,HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0,0,0))    

        while in_Controls:
            window.blit(background_photo,(0,0))
            window.blit(overlay,(0,0))
            fullwindow_text=get_font(15).render("Ctrl + Shift + F : Toggle Fullwindow",True,(255, 255, 255))
            fullwindow_rect=fullwindow_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.2))
            window.blit(fullwindow_text,fullwindow_rect)
            Exit_fullwindow_text=get_font(15).render("Esc : To Pause Game",True,(255, 255, 255))
            Exit_fullwindow_rect=Exit_fullwindow_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.3))
            window.blit(Exit_fullwindow_text,Exit_fullwindow_rect)
            movementright_text=get_font(15).render("D, Right Arrow : To Move Right",True,(255, 255, 255))
            movementright_rect=movementright_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.4))
            window.blit(movementright_text,movementright_rect)
            movementleft_text=get_font(15).render("A, Left Arrow : To Move Left",True,(255, 255, 255))
            movementleft_rect=movementleft_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.5))
            window.blit(movementleft_text,movementleft_rect)
            movementup_text=get_font(15).render("W, Up Arrow : To Move Upward",True,(255, 255, 255))
            movementup_rect=movementup_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.6))
            window.blit(movementup_text,movementup_rect)
            movementdown_text=get_font(15).render("S, Down Arrow : Player Movement",True,(255, 255, 255))
            movementdown_rect=movementdown_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.7))
            window.blit(movementdown_text,movementdown_rect)
            Fire_text=get_font(15).render("Space : To Fire Bullet",True,(255, 255, 255))
            Fire_rect=Fire_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.8))
            window.blit(Fire_text,Fire_rect)
            Exitc_text = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.9), text_input="EXIT", font=get_font(25), base_color=(BLACK), hovering_color=(GREY))
            Exitc_text.changeColor(pygame.mouse.get_pos())
            Exitc_text.update(window)

            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()  
                    if event.type==pygame.MOUSEBUTTONDOWN:
                        if Exitc_text.checkForInput(pygame.mouse.get_pos()):
                            select_sound.play()
                            in_Controls=False
                            Setting_menu(username)
            pygame.display.update()

    while in_option:
        window.blit(background_photo,(0,0))
        window.blit(overlay,(0,0))

        Setting_text= get_font(70).render("SETTINGS",True,(BLACK))
        Setting_rect = Setting_text.get_rect(center=(WIDTH*0.5,HEIGHT*0.3))
        window.blit(Setting_text,Setting_rect)
        

        #MUTE BUTTON
        mute_text="UNMUTE" if is_muted else "MUTE"
        mute_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.5), text_input=mute_text,font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        controls_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.6), text_input="CONTROLS",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        back_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.8), text_input="BACK",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))
        logout_button=Button(image=None,pos=(WIDTH*0.5,HEIGHT*0.7), text_input="LOGOUT",font=get_font(30),base_color=(BLACK),hovering_color=(GREY))

        mute_button.changeColor(pygame.mouse.get_pos())
        mute_button.update(window)
        controls_button.changeColor(pygame.mouse.get_pos())
        controls_button.update(window)
        back_button.changeColor(pygame.mouse.get_pos())
        back_button.update(window)
        logout_button.changeColor(pygame.mouse.get_pos())
        logout_button.update(window)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if mute_button.checkForInput(pygame.mouse.get_pos()):
                    toggle_mute()
                    select_sound.play()
                if controls_button.checkForInput(pygame.mouse.get_pos()):
                    select_sound.play()
                    Controls()
                if back_button.checkForInput(pygame.mouse.get_pos()):
                    select_sound.play()
                    in_option=False
                    set_user_logged_in(username)
                    main(username)
                if logout_button.checkForInput(pygame.mouse.get_pos()):
                    logout_user(username)
                    intro()
        pygame.display.update()

def game_over(score_value, level, username):
    global bullets, boss_bullets, enemies
    mixer.music.stop()
    game_over_music.play()
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))  
    window.blit(background_photo, (0, 0))
    window.blit(overlay, (0, 0))
    
    game_over_text = get_font(70).render("GAME OVER", True, (255, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.3))
    window.blit(game_over_text, game_over_rect)

    final_score_text = get_font(50).render(f"Final Score: {score_value}", True, (BLACK))
    final_score_rect = final_score_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.5))
    window.blit(final_score_text, final_score_rect)
    
    level_text = get_font(50).render(f"Level: {level}", True, (BLACK))
    level_rect = level_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.6))
    window.blit(level_text, level_rect)

    # Add buttons for restarting or quitting
    restart_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), text_input="RESTART", font=get_font(30), base_color=(BLACK), hovering_color=(GREY))
    exit_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.8), text_input="EXIT", font=get_font(30), base_color=(BLACK), hovering_color=(GREY))

    restart_button.changeColor(pygame.mouse.get_pos())
    restart_button.update(window)
    exit_button.changeColor(pygame.mouse.get_pos())
    exit_button.update(window)

    pygame.display.update()

    # Fetch the user's highest score from the database
    highest_score = fetch_highest_score(username)  

    # Check if the current score is higher than the highest score
    if score_value > highest_score:
        update_highest_score(username, score_value)  # Update the database with the new highest score
    

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.checkForInput(event.pos):
                    bullets = []
                    boss_bullets = []
                    enemies = []
                    score_value = 0
                    play_BG_music()
                    gameplay(username, highest_score)  # Pass updated highest score
                elif exit_button.checkForInput(event.pos):
                    select_sound.play()
                    set_user_logged_in(username)
                    main(username)  # Pass updated highest score

def login_signup():
    run = True
    play_ideal_music()
    username = ""
    password = ""
    selected_action = ""  # To track whether the user selects login or signup
    stage = "menu"  # Tracks the current stage: "menu", "username", "password"

    while run:
            window.blit(login_signup_bg, (0, 0))  # Render background for login/signup
            
            if stage == "menu":
                # Render Login/Signup buttons
                login_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.4), 
                                    text_input="LOGIN", font=get_font(40), 
                                    base_color=(BLACK), hovering_color=(GREY))
                signup_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.6), 
                                    text_input="SIGNUP", font=get_font(40), 
                                    base_color=(BLACK), hovering_color=(GREY))

                # Update button colors on hover
                login_button.changeColor(pygame.mouse.get_pos())
                login_button.update(window)
                signup_button.changeColor(pygame.mouse.get_pos())
                signup_button.update(window)

            elif stage == "username":
                # Render username input (max length: 20 characters)
                username_text = login_font(40).render(f"Username: {username}", True, (BLACK))
                window.blit(username_text, (WIDTH * 0.1, HEIGHT * 0.4))

                # Add a back button to go back to the menu
                back_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.8), 
                                    text_input="BACK", font=get_font(40), 
                                    base_color=(BLACK), hovering_color=(GREY))
                back_button.changeColor(pygame.mouse.get_pos())
                back_button.update(window)

            elif stage == "password":
                # Render password input (masked by *)
                password_text = login_font(40).render(f"Password: {'*' * len(password)}", True, (BLACK))
                window.blit(password_text, (WIDTH * 0.1, HEIGHT * 0.4))

                # Show a confirm button only if the password field has content
                if password:
                    action_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), 
                                        text_input="CONFIRM", font=get_font(40), 
                                        base_color=(BLACK), hovering_color=(GREY))
                    action_button.changeColor(pygame.mouse.get_pos())
                    action_button.update(window)

                # Add a back button to go back to the username input stage
                back_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.85), 
                                    text_input="BACK", font=get_font(40), 
                                    base_color=(BLACK), hovering_color=(GREY))
                back_button.changeColor(pygame.mouse.get_pos())
                back_button.update(window)

            # Update the display
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        toggle_fullwindow()  # Handle full-screen toggle

                # Handle button clicks and key inputs for each stage
                if stage == "menu" and event.type == pygame.MOUSEBUTTONDOWN:
                    if login_button.checkForInput(event.pos):
                        selected_action = "login"
                        stage = "username"  # Move to username input
                    elif signup_button.checkForInput(event.pos):
                        selected_action = "signup"
                        stage = "username"  # Move to username input

                elif stage == "username":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:  # Confirm username and move to password stage
                            stage = "password"
                        elif event.key == pygame.K_BACKSPACE:
                            username = username[:-1]  # Handle backspace
                        elif len(username) < 20:  # Limit username to 20 characters
                            username += event.unicode  # Append input character to username

                    # Handle back button click to return to the menu
                    if event.type == pygame.MOUSEBUTTONDOWN and back_button.checkForInput(event.pos):
                        stage = "menu"

                elif stage == "password":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and password:  # Confirm password
                            if selected_action == "login":
                                if login(username, password):  # Perform login
                                    run = False
                                    main(username)  # Launch main game after login
                            elif selected_action == "signup":
                                if signup(username, password):  # Perform signup
                                    run = False
                                    main(username)  # Launch main game after signup
                        elif event.key == pygame.K_BACKSPACE:
                            password = password[:-1]  # Handle backspace
                        elif len(password) < 8:  # Limit password to 8 characters
                            password += event.unicode  # Append input character to password

                    # Handle back button click to return to username input stage
                    if event.type == pygame.MOUSEBUTTONDOWN and back_button.checkForInput(event.pos):
                        stage = "username"

                    # Handle confirm button click (if password is provided)
                    if password and event.type == pygame.MOUSEBUTTONDOWN and action_button.checkForInput(event.pos):
                        if selected_action == "login":
                            if login(username, password):  # Perform login
                                run = False
                                main(username)  # Launch main game after login
                        elif selected_action == "signup":
                            if signup(username, password):  # Perform signup
                                run = False
                                main(username)  # Launch main game after signup

def gameplay(username, highest_score):
    global boss, bullets, boss_bullets, is_muted, fullwindow, background_photo, player, enemies, boss_spawned, level, score_value, Player_animation_steps,number_of_enemies

    run = True
    FPS = 60
    clock = pygame.time.Clock()
    Lives = 3
    bullets = []  # Store bullets fired by player
    boss_bullets = []
    bosses = []  # Store multiple bosses
    boss_count = 1  # Initially, spawn 1 boss
    boss_spawned = False
    enemies = []
    level = 0
    score_value = 0
    player = Player(WIDTH // 2 - 64, HEIGHT - 180, Player_animation_steps)
    number_of_enemies = 5  # Start with 5 enemies
    spawned_enemies = 0  # Initialize spawned_enemies
    boss = None
    spawned_bosses = 0
    invincible = False  # Player is initially not invincible
    last_hit_time = 0   # Tracks when the last life was lost
    invincibility_duration = 2000  # 2 seconds of invincibility in milliseconds
    start_music.play()
    play_BG_music()
    # Function to spawn enemies
    def spawn_enemies(batch_size):
        nonlocal spawned_enemies
        for _ in range(batch_size):
            if spawned_enemies >= number_of_enemies:
                break
            enemy_type = random.randint(0, len(enemy_images) - 1)
            x = random.randrange(50, WIDTH - 150)
            y = random.randrange(-100, -10)
            enemy = Enemy(x, y, enemy_type)
            # Create a rectangle for the new enemy
            new_enemy_rect = pygame.Rect(x, y, enemy.get_width(), enemy.get_height())

            # Check for collisions with existing enemies
            if all(not new_enemy_rect.colliderect(pygame.Rect(enemy.x, enemy.y, enemy.get_width(), enemy.get_height())) for enemy in enemies):
                enemies.append(enemy)
                spawned_enemies += 1
    
    def spawn_bosses(boss_batch_size):
        nonlocal spawned_bosses
        for i in range(boss_batch_size):
            if spawned_bosses >= boss_count:
                break
            boss_type = random.randint(0, len(boss_images) - 1)
            x = random.randrange(WIDTH // 2 - 64 + (i * 100))
            y = random.randrange(50)
            boss = Boss(x, y, boss_type)
            new_boss_rect = pygame.Rect(x, y, boss.get_width(), boss.get_height())
            play_boss_music() 
            mixer.music.queue(BG_music_path )


        if all(not new_boss_rect.colliderect(pygame.Rect(b.x, b.y, b.get_width(), b.get_height())) for b in bosses):
            bosses.append(boss)
            spawned_bosses+=1


    # Function to redraw values (HUD)
    def redraw_values(lives, level, score):
        """Function to redraw the HUD values (lives, level, score, and highest score)."""

        # Clear the screen by redrawing the background
        window.blit(background_photo, (0, 0))
        # Render HUD values
        lives_label = get_font(20).render(f"Lives: {lives}", True, (BLACK))
        level_label = get_font(20).render(f"Level: {level}", True, (BLACK))
        score_label = get_font(20).render(f"Score: {score}", True, (BLACK))
        highest_score_label = get_font(20).render(f"Highest Score: {highest_score}", True, (BLACK))

        # Display the labels on the screen
        window.blit(lives_label, (10, HEIGHT - 30))
        window.blit(level_label, (WIDTH - level_label.get_width() - 10, HEIGHT - 30))
        window.blit(score_label, (WIDTH * 0.4 - score_label.get_width() // 2, HEIGHT - 30))
        window.blit(highest_score_label,(WIDTH * 0.7 - highest_score_label.get_width() // 2, HEIGHT - 30))

        # Draw the player and update its state
        player.draw(window, invincible)
        player.update()

        # Draw all enemies
        for enemy in enemies:
            enemy.draw(window)

        # Draw all bullets
        for bullet in bullets:
            bullet.draw(window)

        # Draw and update all bosses
        for boss in bosses:
            boss.draw(window)
            for bullet in boss_bullets:
                if bullet["state"] == "fire":
                    window.blit(boss.bullet_img, (bullet["x"], bullet["y"]))

        # Only one call to update the display after all drawings
        pygame.display.update()


    while run:
        clock.tick(FPS)
        redraw_values(Lives, level, score_value)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    player.x_vel = -25
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    player.x_vel = 25
                elif event.key in (pygame.K_UP, pygame.K_w):
                    player.y_vel = -25
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    player.y_vel = 25
                elif event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    toggle_fullwindow()
                elif event.key == pygame.K_SPACE:
                    if not is_muted:
                        bullet_sound.play()
                    fire_bullet(player.x + player.get_width() // 2 - 19, player.y + player.get_height() // 2 - 150)
                elif event.key == pygame.K_ESCAPE:
                    pause_game(username)

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_UP, pygame.K_w, pygame.K_s):
                    player.x_vel = 0
                    player.y_vel = 0

        player.x += player.x_vel
        player.y += player.y_vel
        player.x = max(0, min(player.x, WIDTH - player.get_width()))
        player.y = max(0, min(player.y, HEIGHT - player.get_height()))

        player_rect = pygame.Rect(player.x, player.y, player.get_width(), player.get_height())

        for bullet in bullets[:]:
            bullet.update()
            bullet.draw(window)

            if bullet.y < 0:
                bullets.remove(bullet)
                continue

            bullet_rect = pygame.Rect(bullet.x, bullet.y, bullet.get_width(), bullet.get_height())

            for enemy in enemies[:]:
                if isCollision(bullet_rect, pygame.Rect(enemy.x, enemy.y, enemy.get_width(), enemy.get_height())):
                    enemies.remove(enemy)
                    bullets.remove(bullet)
                    explosion_sound.play()
                    score_value += 1
                    break

            for boss in bosses[:]:
                if isCollision(bullet_rect, pygame.Rect(boss.x, boss.y, boss.get_width(), boss.get_height())):
                    boss.health -= 1
                    if boss.health <= 0:
                        bosses.remove(boss)
                        score_value += 5
                        boss_spawned = False

                    try:
                        bullets.remove(bullet)
                    except ValueError:
                        print("Warning: Bullet already removed or not found in the list.")
                    
                    play_explosion_sound()

        for enemy in enemies[:]:
            enemy.move(vel=1)
            if enemy.y > HEIGHT:
                score_value -= 1
                enemies.remove(enemy)
            
            # Check for collision with the player
            if player_rect.colliderect(pygame.Rect(enemy.x, enemy.y, enemy.get_width(), enemy.get_height())):
                if not invincible:
                    Lives -= 1
                    last_hit_time = pygame.time.get_ticks()

                    # Check if the player has no more lives
                    if Lives <= 0:
                        game_over(score_value, level, username)
                        return

                # Remove the enemy regardless of invincibility
                enemies.remove(enemy)


        if len(enemies) == 0 and not boss_spawned:
            level += 1
            spawned_enemies = 0

            if level % 5 == 0:
                # Spawn bosses when the level is a multiple of 2
                spawn_bosses(boss_count)
                boss_bullets=[]
                boss_spawned = True
                boss_count += 1
            else:
                # Ensure to spawn 5 enemies at a time when not a boss level
                number_of_enemies += 1
                boss_bullets=[]
                spawn_enemies(0)

        # After all bosses are defeated, reset the boss_spawned flag to spawn new bosses in future levels
        if boss_spawned and len(bosses) == 0:
            boss_count+=1
            boss_spawned = False


        if spawned_enemies < number_of_enemies and not boss_spawned:
            spawn_enemies(5)  # Spawn additional enemies as the previous ones move down


        for boss in bosses[:]:
            boss.move()
            boss.shoot()


            for boss_bullet in boss_bullets[:]:
                boss_bullet["y"] += 5
                if boss_bullet["y"] > HEIGHT:
                    boss_bullets.remove(boss_bullet)

                boss_bullet_rect = pygame.Rect(boss_bullet["x"], boss_bullet["y"], boss.bullet_img.get_width(), boss.bullet_img.get_height())
                if player_rect.colliderect(boss_bullet_rect):
                    Lives -= 1
                    boss_bullets.remove(boss_bullet)
                    last_hit_time = pygame.time.get_ticks()
                    if Lives <= 0:
                        game_over(score_value, level, username)
                        return

        if Lives < 3:
            if pygame.time.get_ticks() - last_hit_time > invincibility_duration:
                invincible = False
            else:
                invincible = True

        if score_value > highest_score:
            highest_score = score_value
            update_highest_score(username, highest_score)

    pygame.quit()
    sys.exit()

def main(username):
    # Fetch the highest score from the database
    highest_score = fetch_highest_score(username)
    play_ideal_music()
    

    while True:
        
        window.blit(background_photo, (0, 0))

        # Title and buttons
        title_text = get_font(70).render("SPACE INVADERS", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.2))
        window.blit(title_text, title_rect)
        
        start_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.5), text_input="START", font=get_font(40), base_color=(BLACK), hovering_color=(GREY))
        Setting_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.6), text_input="SETTINGS", font=get_font(40), base_color=(BLACK), hovering_color=(GREY))
        exit_button = Button(image=None, pos=(WIDTH * 0.5, HEIGHT * 0.7), text_input="EXIT", font=get_font(40), base_color=(BLACK), hovering_color=(GREY))

        # Render buttons
        start_button.changeColor(pygame.mouse.get_pos())
        start_button.update(window)
        Setting_button.changeColor(pygame.mouse.get_pos())
        Setting_button.update(window)
        exit_button.changeColor(pygame.mouse.get_pos())
        exit_button.update(window)

        # Display the highest score
        highest_score_text = get_font(30).render(f"Highest Score: {highest_score}", True, (255, 255, 255))
        highest_score_rect = highest_score_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.4))
        window.blit(highest_score_text, highest_score_rect)
        #Display the username
        name_text = get_font(30).render(f"Welcome {username}.", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.3))
        window.blit(name_text, name_rect)
        #Display the version
        version_text = get_font(10).render("Version 1.0", True, (0, 0, 0))
        version_rect = version_text.get_rect(center=(WIDTH * 0.9, HEIGHT * 0.9))
        window.blit(version_text, version_rect)


        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_database()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    toggle_fullwindow()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.checkForInput(event.pos):
                    start_music.play()
                    # Call gameplay and update highest score
                    highest_score = gameplay(username, highest_score)
                elif Setting_button.checkForInput(event.pos):
                    select_sound.play()
                    Setting_menu(username)
                elif exit_button.checkForInput(event.pos):
                    select_sound.play()
                    check_logged_in_user()
                    close_database()
                    pygame.quit()
                    sys.exit()

intro()