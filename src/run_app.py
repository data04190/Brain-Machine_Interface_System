__all__ = ['main']

from subprocess import run
import pygame
import pygame_menu
import random
from threading import Thread
from pygame_menu.examples import create_example_window
from typing import Optional
from config import load_parameters
from socket_thread import socket_thread

# -----------------------------------------------------------------------------
# Constants and global variables
# -----------------------------------------------------------------------------

# parameters from config.json
FPS = 60
WINDOW_SIZE = [1280, 720]
load_parameters(globals())

# parameters, not loaded by config.json
running = [True]
game_info = []
screen_width, screen_height = WINDOW_SIZE
ABOUT = ['pygame-menu {0}'.format(pygame_menu.__version__),
         'Author: {0}'.format(pygame_menu.__author__),
         'Email: {0}'.format(pygame_menu.__email__)]
clock: Optional['pygame.time.Clock'] = None
main_menu: Optional['pygame_menu.Menu'] = None
surface: Optional['pygame.Surface'] = None
screen: Optional['pygame.Surface'] = None

pygame.init()
bg_color = pygame.Color('#2F373F')
accent_color = (27,35,43)
basic_font = pygame.font.Font('freesansbold.ttf', 32)
plob_sound = pygame.mixer.Sound("res/pong.ogg")
score_sound = pygame.mixer.Sound("res/score.ogg")

event_fix = pygame.USEREVENT
event_up = pygame.USEREVENT+1
event_down = pygame.USEREVENT+2
event_moveup = pygame.USEREVENT+3
event_movedown = pygame.USEREVENT+4
event_moveup_train = pygame.USEREVENT+5
event_movedown_train = pygame.USEREVENT+6

# -----------------------------------------------------------------------------
# Classes and Methods
# -----------------------------------------------------------------------------
class Block(pygame.sprite.Sprite):
    def __init__(self,path,x_pos,y_pos):
        super().__init__()
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(center = (x_pos,y_pos))

class Player(Block):
    def __init__(self,path,x_pos,y_pos,speed):
        super().__init__(path,x_pos,y_pos)
        self.speed = speed
        self.movement = 0

    def screen_constrain(self):
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= screen_height:
            self.rect.bottom = screen_height

    def update(self,ball_group):
        self.rect.y += self.movement
        self.screen_constrain()

class Ball(Block):
    def __init__(self,path,x_pos,y_pos,speed_x,speed_y,paddles):
        super().__init__(path,x_pos,y_pos)
        self.speed_x = speed_x * random.choice((-1,1))
        self.speed_y = speed_y * random.choice((-1,1))
        self.paddles = paddles
        self.active = False
        self.score_time = 0

    def update(self):
        if self.active:
            self.rect.x += self.speed_x
            self.rect.y += self.speed_y
            self.collisions()
        else:
            self.restart_counter()
        
    def collisions(self):
        if self.rect.top <= 0 or self.rect.bottom >= screen_height:
            pygame.mixer.Sound.play(plob_sound)
            self.speed_y *= -1

        if pygame.sprite.spritecollide(self,self.paddles,False):
            pygame.mixer.Sound.play(plob_sound)
            collision_paddle = pygame.sprite.spritecollide(self,self.paddles,False)[0].rect
            if abs(self.rect.right - collision_paddle.left) < 10 and self.speed_x > 0:
                self.speed_x *= -1
            if abs(self.rect.left - collision_paddle.right) < 10 and self.speed_x < 0:
                self.speed_x *= -1
            if abs(self.rect.top - collision_paddle.bottom) < 10 and self.speed_y < 0:
                self.rect.top = collision_paddle.bottom
                self.speed_y *= -1
            if abs(self.rect.bottom - collision_paddle.top) < 10 and self.speed_y > 0:
                self.rect.bottom = collision_paddle.top
                self.speed_y *= -1

    def reset_ball(self):
        self.active = False
        self.speed_x *= random.choice((-1,1))
        self.speed_y *= random.choice((-1,1))
        self.score_time = pygame.time.get_ticks()
        self.rect.center = (screen_width/2,screen_height/2)
        pygame.mixer.Sound.play(score_sound)

    def restart_counter(self):
        current_time = pygame.time.get_ticks()
        countdown_number = 3

        if current_time - self.score_time <= 700:
            countdown_number = 3
        if 700 < current_time - self.score_time <= 1400:
            countdown_number = 2
        if 1400 < current_time - self.score_time <= 2100:
            countdown_number = 1
        if current_time - self.score_time >= 2100:
            self.active = True

        time_counter = basic_font.render(str(countdown_number),True,accent_color)
        time_counter_rect = time_counter.get_rect(center = (screen_width/2,screen_height/2 + 50))
        pygame.draw.rect(screen,bg_color,time_counter_rect)
        screen.blit(time_counter,time_counter_rect)

class Opponent(Block):
    def __init__(self,path,x_pos,y_pos,speed):
        super().__init__(path,x_pos,y_pos)
        self.speed = speed

    def update(self,ball_group):
        if self.rect.top < ball_group.sprite.rect.y:
            self.rect.y += self.speed
        if self.rect.bottom > ball_group.sprite.rect.y:
            self.rect.y -= self.speed
        self.constrain()

    def constrain(self):
        if self.rect.top <= 0: self.rect.top = 0
        if self.rect.bottom >= screen_height: self.rect.bottom = screen_height

class GameManager:
    def __init__(self,ball_group,paddle_group):
        self.player_score = 0
        self.opponent_score = 0
        self.ball_group = ball_group
        self.paddle_group = paddle_group

    def run_game(self):
        # Drawing the game objects
        self.paddle_group.draw(screen)
        self.ball_group.draw(screen)

        # Updating the game objects
        self.paddle_group.update(self.ball_group)
        self.ball_group.update()
        self.reset_ball()
        self.draw_score()

    def reset_ball(self):
        if self.ball_group.sprite.rect.right >= screen_width:
            self.opponent_score += 1
            self.ball_group.sprite.reset_ball()
        if self.ball_group.sprite.rect.left <= 0:
            self.player_score += 1
            self.ball_group.sprite.reset_ball()

    def draw_score(self):
        player_score = basic_font.render(str(self.player_score),True,accent_color)
        opponent_score = basic_font.render(str(self.opponent_score),True,accent_color)

        player_score_rect = player_score.get_rect(midleft = (screen_width / 2 + 40,screen_height/2))
        opponent_score_rect = opponent_score.get_rect(midright = (screen_width / 2 - 40,screen_height/2))

        screen.blit(player_score,player_score_rect)
        screen.blit(opponent_score,opponent_score_rect)

def train_function():

    global running, event_fix, event_up, event_down, event_moveup, event_movedown

    size = WINDOW_SIZE
    black = 0,0,0
    white = pygame.Color('white')
    blue = pygame.Color('blue')
    yellow = pygame.Color('yellow')
    radius = size[1]//60

    screen = pygame.display.set_mode(size)

    pos = [(size[0]//2, size[1]//2-size[1]//12*i) for i in range(-5,6)]

    flags = [True, True]
    from session import session_train
    t = Thread(target=session_train, args=[flags, (event_down, event_up, event_fix, 
                                                    event_movedown_train, event_moveup_train)])
    t.start()

    fix = True
    idx = 0
    cur = 5
    while flags[0]:
        for event in pygame.event.get():
            if event.type == event_fix:
                fix = True
                cur = 5
            if event.type == event_up:
                fix = False
                idx = 10
            if event.type == event_down:
                fix = False
                idx = 0
            if event.type == event_moveup_train:
                if flags[1]:
                    cur = min(cur+1, 10)
                    if cur==idx: flags[1] = False
            if event.type == event_movedown_train:
                if flags[1]:
                    cur = max(cur-1, 0)
                    if cur==idx: flags[1] = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                flags[0] = False
                break
            if event.type == pygame.QUIT:
                flags[0] = False
                running[0] = False
                exit()

        screen.fill(black)

        fix_color = white if fix else black
        pygame.draw.line(screen, fix_color, (size[0]//2-50, size[1]//2),
                                        (size[0]//2+50, size[1]//2))
        pygame.draw.line(screen, fix_color, (size[0]//2, size[1]//2-50),
                                        (size[0]//2, size[1]//2+50))
                
        if not fix:
            colors = [white]*11
            colors[idx] = blue
            colors[cur] = yellow
            for i in range(11):
                pygame.draw.circle(screen, colors[i], pos[i], radius)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

    main_menu.enable()

def test_function():

    global running, event_fix, event_up, event_down, event_moveup, event_movedown

    size = WINDOW_SIZE
    black = 0,0,0
    white = pygame.Color('white')
    blue = pygame.Color('blue')
    yellow = pygame.Color('yellow')
    radius = size[1]//60

    screen = pygame.display.set_mode(size)

    pos = [(size[0]//2, size[1]//2-size[1]//12*i) for i in range(-5,6)]

    flags = [True, True]
    from session import session_test
    t = Thread(target=session_test, args=[flags, (event_down, event_up, event_fix)])
    t.start()

    fix = True
    idx = 0
    cur = 5
    while flags[0]:
        for event in pygame.event.get():
            if event.type == event_fix:
                fix = True
                cur = 5
            if event.type == event_up:
                fix = False
                idx = 10
            if event.type == event_down:
                fix = False
                idx = 0
            if event.type == event_moveup or\
                (event.type == pygame.KEYDOWN and event.key==pygame.K_UP):
                if flags[1] and not fix:
                    cur = min(cur+1, 10)
                    if cur==idx: flags[1] = False
            if event.type == event_movedown or\
                (event.type == pygame.KEYDOWN and event.key==pygame.K_DOWN):
                if flags[1] and not fix:
                    cur = max(cur-1, 0)
                    if cur==idx: flags[1] = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                main_menu.enable()
                # Quit this function, then skip to loop of main-menu
                return
            if event.type == pygame.QUIT:
                flags[0] = False
                running[0] = False
                exit()

        screen.fill(black)

        fix_color = white if fix else black
        pygame.draw.line(screen, fix_color, (size[0]//2-50, size[1]//2),
                                        (size[0]//2+50, size[1]//2))
        pygame.draw.line(screen, fix_color, (size[0]//2, size[1]//2-50),
                                        (size[0]//2, size[1]//2+50))
                
        if not fix:
            colors = [white]*11
            colors[idx] = blue
            colors[cur] = yellow
            for i in range(11):
                pygame.draw.circle(screen, colors[i], pos[i], radius)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    
    main_menu.enable()

def play_function() -> None:
    # Define globals
    global main_menu
    global clock

    global running, game_info

    # Variables
    middle_strip = pygame.Rect(screen_width/2 - 2,0,4,screen_height)

    # Game objects
    player = Player('res/Paddle.png',screen_width - 20,screen_height/2,5)
    opponent = Opponent('res/Paddle.png',20,screen_width/2,5)
    paddle_group = pygame.sprite.Group()
    paddle_group.add(player)
    paddle_group.add(opponent)

    ball = Ball('res/Ball.png',screen_width/2,screen_height/2,4,4,paddle_group)
    ball_sprite = pygame.sprite.GroupSingle()
    ball_sprite.add(ball)

    game_info.append(player.rect)
    game_info.append(ball.rect)

    game_manager = GameManager(ball_sprite,paddle_group)

    # Reset main menu and disable
    # You also can set another menu, like a 'pause menu', or just use the same
    # main_menu as the menu that will check all your input.
    main_menu.disable()
    main_menu.full_reset()

    frame = 0
    while True:
        # noinspection PyUnresolvedReferences
        clock.tick(FPS)
        frame += 1

        # Application events
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running[0] = False
                exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    player.movement -= player.speed
                if e.key == pygame.K_DOWN:
                    player.movement += player.speed
                if e.key == pygame.K_ESCAPE:
                    main_menu.enable()
                    # Quit this function, then skip to loop of main-menu

                    game_info.pop()
                    game_info.pop()

                    return
            if e.type == pygame.KEYUP:
                if e.key == pygame.K_UP:
                    player.movement += player.speed
                if e.key == pygame.K_DOWN:
                    player.movement -= player.speed
            if e.type == event_moveup:
                player.movement = -player.speed
            if e.type == event_movedown:
                player.movement = player.speed

        # Pass events to main_menu
        if main_menu.is_enabled():
            main_menu.update(events)
        
        # Background Stuff
        screen.fill(bg_color)
        pygame.draw.rect(screen,accent_color,middle_strip)
        
        # Run the game
        game_manager.run_game()

        # Rendering
        pygame.display.flip()

def main_background() -> None:
    global surface
    surface.fill((0, 0, 0))

def main() -> None:
    # -------------------------------------------------------------------------
    # Globals
    # -------------------------------------------------------------------------
    global clock
    global main_menu
    global surface
    global screen

    global running, event_fix, event_up, event_down, event_moveup, event_movedown, game_info

    # -------------------------------------------------------------------------
    # Create window
    # -------------------------------------------------------------------------
    surface = create_example_window('Mind Pong', WINDOW_SIZE)
    screen = surface
    clock = pygame.time.Clock()

    # -------------------------------------------------------------------------
    # Create menus: Main
    # -------------------------------------------------------------------------
    main_theme = pygame_menu.themes.THEME_DEFAULT.copy()

    main_menu = pygame_menu.Menu(
        height=WINDOW_SIZE[1] * 0.6,
        theme=main_theme,
        title='Main Menu',
        width=WINDOW_SIZE[0] * 0.6
    )

    main_menu.add.button('Train', train_function)
    main_menu.add.button('Test', test_function)
    main_menu.add.button('Game', play_function)

    t = Thread(target=socket_thread, args=[running, (event_moveup, event_movedown), game_info])
    t.start()

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------
    while True:
        # Tick
        clock.tick(FPS)

        # Paint background
        main_background()

        # Application events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                # running[0] = False
                exit()

        # Main menu
        if main_menu.is_enabled():
            main_menu.mainloop(surface, main_background, fps_limit=FPS)

        # Flip surface
        pygame.display.flip()

if __name__ == '__main__':
    main()