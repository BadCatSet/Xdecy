import random
import pygame_menu
import pygame
import os
import sys
from pygame import KEYDOWN, Rect, Vector2
from pygame.transform import scale as pg_scale


# заглушки чтоб можно было объявить константы
class Zombie:
    pass


class Skeleton:
    pass


class Spider:
    pass


class Mag:
    pass


pygame.init()
MONITOR_SIZE = pygame.display.Info().current_w, pygame.display.Info().current_h
DISPLAY_S = DISPLAY_W, DISPLAY_H = min(MONITOR_SIZE), min(MONITOR_SIZE)

screen = pygame.display.set_mode(MONITOR_SIZE)

cell_s = 10  # temporary
half = cell_s / 2
quarter = cell_s / 4
half_d = (half, half)  # half doubled
cell_ss = (cell_s, cell_s)
quarter_d = (quarter, quarter)  # quarter doubled

SPLASH_POTION_AMPLIFIER = 100

SWORD_DAMAGE = -50

ARROW_DEFAULT_COOLDOWN = 500
ARROW_MAX_COOLDOWN = -5000
SWORD_DEFAULT_COOLDOWN = 360

TT_COLOR = [(255, 70, 70), (255, 255, 70)]

PICK_PRIORITY = ['item_gold_heart', 'item_heart', 'item_healing_potion', 'item_arrow']
LOOT_LIST = ['item_healing_potion', 'item_arrow', 'item_gold_heart', 'item_heart']
DROP_AMOUNT = [(1, 4), (2, 6), (10, 20), (15, 30)]

DROP_CHANCES = {Skeleton: [0.1, 0.6, 0.05, 0.1],
                Zombie: [0.1, 0.2, 0.1, 0.3],
                Spider: [0.2, 0.0, 0.2, 0.7],
                Mag: [0.2, 0.1, 0.5, 0.05]}  # temporary

FREQUENCY_BG = [400, 1, 1, 1, 1, 1, 1, 1]

fire_cooldown = ARROW_MAX_COOLDOWN
sword_cooldown = 0
sword_angle = 0
all_time = 0

projectiles = []
temp_text = []
mag_circles = []
window_stack = ['menu']

shlopa_ending = False
difficulty = 1

last_given_uid = -1

BLACK = pygame.Color('black')
WHITE = pygame.Color('white')
GREEN = pygame.Color('green')


def set_difficulty(selected, value):
    global difficulty
    difficulty = value


def stack_add_game():
    window_stack.append('game')
    menu.disable()


def terminate():
    pygame.quit()
    exit()


menu = pygame_menu.Menu('Xdecy', *MONITOR_SIZE, theme=pygame_menu.themes.THEME_BLUE)
menu.add.selector('Difficulty: ', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)
menu.add.button('Play', stack_add_game)
menu.add.button('Quit', pygame_menu.events.EXIT)


def set_cell_size(ncs):
    global cell_s, half, quarter, cell_ss, half_d, quarter_d

    cell_s = ncs  # temporary
    half = cell_s / 2
    quarter = cell_s / 4
    half_d = (half, half)  # half doubled
    cell_ss = (cell_s, cell_s)
    quarter_d = (quarter, quarter)  # quarter doubled


def get_uid():
    global last_given_uid
    last_given_uid += 1
    return last_given_uid


def load_image(fullname, colorkey=None, size=None):
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)
    if size is not None:
        image = pg_scale(image, size)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((1, 1))
        image.set_colorkey(colorkey)

    return image.convert()


class Assets:
    PATH = ''
    COUNT_BACKGROUND = 7
    COUNT_HARD = 3
    COUNT_SOFT = 1
    NAME_HALF_S = ['steve', 'zombie', 'skeleton', 'spider', 'mag', 'poison', 'regeneration',
                   'item_healing_potion', 'item_arrow']
    NAME_QUARTER_S = ['item_gold_heart', 'item_heart']
    NAME_ARROW = 'arrow'

    NAME_SOUNDS = ['death sound', 'hit', 'shlopa sound']

    def __init__(self, path):
        self.PATH = path
        for i in range(self.COUNT_BACKGROUND):
            image = load_image(path + 'b' + str(i) + '.png', size=cell_ss)
            self.__setattr__('b' + str(i), image)

        for i in range(self.COUNT_HARD):
            image = load_image(path + 'h' + str(i) + '.png', size=cell_ss)
            self.__setattr__('h' + str(i), image)

        for i in range(self.COUNT_SOFT):
            image = load_image(path + 's' + str(i) + '.png', size=cell_ss)
            self.__setattr__('s' + str(i), image)

        for i in self.NAME_HALF_S:
            image = load_image(path + i + '.png', size=cell_ss)
            self.__setattr__(i, image)
        for i in self.NAME_QUARTER_S:
            image = load_image(path + i + '.png', size=quarter_d)
            self.__setattr__(i, image)

        self.arrow = load_image(path + self.NAME_ARROW + '.png', size=(cell_s, cell_s * 3 // 8))

        for i in self.NAME_SOUNDS:
            sound = pygame.mixer.Sound(path + i + '.wav')
            self.__setattr__(i, sound)


class Locations:
    def __init__(self, path):
        with open(path + '') as file:
            data = file.readlines()


class Arrow:
    pass


class Item:
    pass


class Effect:
    pass


class Entity(pygame.sprite.Sprite):
    loot = [0, 0, 0, 0]

    def get_loot(self):
        loot = self.loot
        for d in enumerate(loot):
            if random.random() < d[1]:
                pass
    #            location.items.append(Item(self.r.x, self.r.y, LOOT_LIST[d[0]],
    #                                      int(random.randrange(10, 30) // difficulty + 1)))
    #    location.enemies.remove(i)


class Player(Entity):
    pass


class Zombie(Entity):
    pass


class Skeleton(Entity):
    pass


class Spider(Entity):
    pass


class Mag(Entity):
    pass


class MagCircle:
    pass


class TempText:
    pass


def run_game():
    keys = pygame.key.get_pressed()
    mods = pygame.key.get_mods()
    mouse = pygame.mouse.get_pressed(3)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        if event.type == KEYDOWN:
            if event.key == pygame.K_ESCAPE and mods & pygame.KMOD_SHIFT:
                terminate()
    draw_game()


def draw_game():
    screen.fill(BLACK)
    pygame.draw.circle(screen, WHITE, (100, 100), 40)
    pygame.display.flip()


def run_menu():
    menu.mainloop(screen)


def run_loose():
    pass


assets = Assets('assets2/')

if __name__ == "__main__":
    while True:
        if window_stack[-1] == 'menu':
            run_menu()
        if window_stack[-1] == 'game':
            run_game()
