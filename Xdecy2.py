# попытка не переписывать программу, а изменить
"""
v1.1
"""

from math import sin
import os
import random

# use normal way to load pathfinding
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import pygame
from pygame import Rect
from pygame.transform import scale as pg_scale


# use alternative way to load pathfinding
# from tpath import AStarFinder, DiagonalMovement, Grid

def get_uid():
    global last_given_uid
    last_given_uid += 1
    return last_given_uid


def terminate():
    pygame.quit()
    exit()


def set_cell_size(new_cell_size):
    global cell_s, half, quarter, cell_ss, half_d, quarter_d, player_radius, splash_potion_radius, \
        enemy_radius, arrow_size
    cell_s = new_cell_size
    half = cell_s / 2
    quarter = cell_s / 4
    half_d = (half, half)  # half doubled
    cell_ss = (cell_s, cell_s)
    quarter_d = (quarter, quarter)  # quarter doubled
    player_radius = 1.25
    splash_potion_radius = 1.2
    enemy_radius = 1
    arrow_size = (cell_s, cell_s * 3 // 8)


class Assets:
    PATH = ''
    FREQUENCY_BG = [400, 1, 1, 1, 1, 1, 1, 1, 1]
    NAME_BACKGROUND = ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8']
    NAME_HARD = ['h0', 'h1', 'h2']
    NAME_SOFT = ['s0']
    NAME_HALF_S = ['steve', 'zombie', 'skeleton', 'spider', 'mag', 'poison', 'regeneration',
                   'item_healing_potion', 'item_arrow']
    NAME_QUARTER_S = ['item_gold_heart', 'item_heart']
    NAME_ARROW = 'arrow'

    NAME_SOUNDS = ['death_sound', 'hit', 'shlopa_sound']

    NAME_MONITOR_S = ['death_screen', 'shlopa_screen']

    def __init__(self, path):
        self.PATH = path
        for i in self.NAME_BACKGROUND + self.NAME_HARD + self.NAME_SOFT:
            self.load_image(i, cell_ss)

        for i in self.NAME_HALF_S:
            self.load_image(i, half_d)

        for i in self.NAME_QUARTER_S:
            self.load_image(i, quarter_d)
        for i in self.NAME_MONITOR_S:
            self.load_image(i, monitor_size)

        self.load_image(self.NAME_ARROW, arrow_size)
        self.item_arrow.set_colorkey((255, 255, 255))
        self.item_gold_heart.set_colorkey((255, 255, 255))
        self.item_heart.set_colorkey((255, 255, 255))

        for i in self.NAME_SOUNDS:
            sound = pygame.mixer.Sound(path + i + '.wav')
            self.__setattr__(i, sound)

    def load_image(self, name, im_size=None, colorkey=None, filetype='.png'):
        fullname = os.path.join(self.PATH, name + filetype)
        if not os.path.isfile(fullname):
            print(f"Файл с изображением '{fullname}' не найден")
            terminate()

        image = pygame.image.load(fullname)
        if size is not None:
            image = pg_scale(image, im_size)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((1, 1))
            image.set_colorkey(colorkey)
        self.__setattr__(name, image)

    def get_bg(self):
        return random.choices(self.NAME_BACKGROUND, weights=self.FREQUENCY_BG, k=1)[0]


class MyGroup(pygame.sprite.Group):
    def draw(self, surface: pygame.Surface):
        for i in self.sprites():
            i.draw(surface)


class MySprite(pygame.sprite.Sprite):
    def draw(self, surface: pygame.Surface):
        pass


class Cell(MySprite):
    def __init__(self, x, y, tile, owner):
        print('init! cell')
        if tile == 'b0':
            super().__init__(owner.bg_group)
            tile = assets.get_bg()
        else:
            super().__init__(owner.block_group)

        self.tile = tile
        self.rect = Rect(x, y, 1, 1)
        self.image = eval(f'assets.{tile}')

    def draw(self, surface: pygame.Surface):
        coord = (self.rect.x * cell_s, self.rect.y * cell_s)
        print(coord)
        surface.blit(self.image, coord)


class Location:
    def __init__(self, cells, enemies, items):
        self.bg_group = MyGroup()
        self.block_group = MyGroup()  # hard and soft
        self.cells = [[Cell(x, y, cells[x][y], self) for y in range(size)] for x in range(size)]
        self.enemies = enemies
        self.items = items

    def __setitem__(self, c, value):
        self.cells[c[0]][c[1]] = value

    def __getitem__(self, c):
        return self.cells[c[0]][c[1]]

    def __repr__(self):
        return self.__dict__


class Arrow:
    def __init__(self, x, y, dx, dy, speed):

        self.x = x
        self.y = y
        self.d = pygame.Vector2(dx, dy).normalize() * (speed // -300 + 0.2)
        self.angle = self.d.as_polar()[1]

        self.uid = get_uid()

        self.image = pygame.transform.rotate(assets.arrow, -self.angle)
        self.image.set_colorkey((255, 255, 255))

        rrr = self.image.get_rect()
        tv = pygame.Vector2()
        tv.from_polar((arrow_size[0] // 2, self.angle - 5))
        self.image_dx = - rrr.centerx - tv.x
        self.image_dy = - rrr.centery - tv.y

        self.damage = -count_damage(speed)

        self.forbidden_damages = []

    def update(self, cells):
        self.x += self.d.x
        self.y += self.d.y

        if not (0 <= self.x <= size and 0 <= self.y <= size):
            projectiles.remove(self)
            return

        tx, ty = int(self.x // cell_s), int(self.y // cell_s)
        if 0 <= tx < len(cells) and 0 <= ty < len(cells):
            if cells[tx][ty] in assets.NAME_SOFT:
                projectiles.remove(self)
                locations[(pl.lx, pl.ly)][tx, ty] = assets.get_bg()
                return True
            if cells[tx][ty] in assets.NAME_HARD:
                projectiles.remove(self)

    def draw(self, surface: pygame.Surface):
        pass  # todo


class Item:
    def __init__(self, x, y, item, amount):
        self.x = x
        self.y = y
        self.start_time = all_time + random.randrange(-1000, 1000)
        self.image = assets.__dict__[item]
        self.dx = self.image.get_rect().centerx
        self.dy = self.image.get_rect().centery

        self.item = item
        self.amount = amount

    def can_pick(self):
        return collision_with_circle(pl, self.x, self.y, player_radius)

    def pick(self):
        if self.item == 'item_healing_potion':
            pl.potions += self.amount
        if self.item == 'item_arrow':
            pl.arrows += self.amount
        if self.item == 'item_gold_heart':
            delta = self.amount * random.randrange(1, 3)
            pl.max_health += delta
            temp_text.append(
                TempText(pl.rect.x + quarter, pl.rect.y + quarter, str(delta), (225, 215, 0)))
        if self.item == 'item_heart':
            pl.apply_damage(self.amount)

    def draw(self, surface: pygame.Surface):
        offset = sin((all_time + self.start_time) / 300) * 10
        surface.blit(self.image, (self.x * cell_s, self.y * cell_s + offset))
        surface.blit(get_text(str(self.amount)), (self.x * cell_s, self.y * cell_s + offset))

    def __repr__(self):
        return f"{type(self).__name__}({self.x}, {self.y}, '{self.item}', {self.amount})"


class Effect:
    def __init__(self, sort, time, amplifier, cooldown):
        self.time_to_del = all_time + time
        self.sort = sort
        self.amplifier = amplifier
        self.cooldown = all_time
        self.max_cooldown = cooldown

    def get(self):
        if self.cooldown < all_time:
            self.cooldown += self.max_cooldown
            if self.sort == 'health':
                return 'health', self.amplifier * (self.cooldown - all_time)
        return 'health', 0

    def check(self):
        return self.time_to_del < all_time


class Entity:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 1, 1)
        self.image = None

        self.max_health = 0
        self.health = self.max_health

        self.effects = []
        self.speed = 0

        self.uid = get_uid()

    def apply_damage(self, delta):
        global temp_text
        delta = min(self.health + delta, self.max_health) - self.health
        self.health += delta
        if int(delta) < 0:
            pygame.mixer.Sound.play(assets.hit)
        if int(delta):
            temp_text.append(TempText(self.rect.centerx, self.rect.centery, str(int(delta)),
                                      TT_COLOR[1 if self.uid else 0]))

    def check_damage_arrow(self):
        for i in projectiles:
            if self.rect.collidepoint(i.x, i.y):
                if self.uid not in i.forbidden_damages:
                    i.forbidden_damages.append(self.uid)
                    if self.health > 0:
                        self.apply_damage(i.damage)
                        if self.health <= 0:
                            projectiles.remove(i)

    def update(self, cells):
        for i in self.effects:
            t = i.get()
            if t[0] == 'health':
                self.apply_damage(t[1])

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, (self.rect.x * cell_s, self.rect.y * cell_s))

    def draw_health(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (100, 100, 100), (self.rect.x * cell_s,
                                                    self.rect.y * cell_s - 10, half, 5))
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x * cell_s, self.rect.y * cell_s - 10,
                                                half * self.health // self.max_health, 5))
        surface.blit(get_text(str(int(self.health))),
                     (self.rect.x * cell_s, self.rect.y * cell_s - 15))

    def __repr__(self):
        return self.__dict__


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.steve
        self.lx = 0
        self.ly = 0
        self.max_health = 200
        self.health = self.max_health
        self.speed = 1 / FPS
        self.potions = 0
        self.arrows = 0

    def move(self, dx, dy):
        dx = dx * self.speed
        dy = dy * self.speed
        dlx, dly = 0, 0
        if 0 <= self.rect.x + dx <= size - 0.5:
            if not any_collisions(self, dx, 0):
                self.rect.x += dx
            elif not any_collisions(self, dx // abs(dx), 0):
                self.rect.x += dx // abs(dx)
        else:
            dlx = -1 if self.rect.x + dx < 0 else 1

        if 0 <= self.rect.y + dy <= size - 0.5:
            if not any_collisions(self, 0, dy):
                self.rect.y += dy
            elif not any_collisions(self, 0, dy // abs(dy)):
                self.rect.y += dy // abs(dy)
        else:
            dly = -1 if self.rect.y + dy < 0 else 1
        return dlx, dly


class Zombie(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.zombie
        self.max_cooldown = 500
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.8 / FPS
        self.damage = -11 * difficulty
        self.max_health = 500 * difficulty
        self.health = self.max_health

    def update(self, cells):
        super().update(cells)

        if self.cooldown < all_time:
            if (self.rect.x - pl.rect.x) ** 2 + (self.rect.y - pl.rect.y) ** 2 < enemy_radius ** 2:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage + random.randrange(-5, 9))

        if (pl.rect.x - self.rect.x) ** 2 + (pl.rect.y - self.rect.y) ** 2 >= cell_s ** 2:
            act = find_path(cells, (self.rect.x, self.rect.y),
                            (pl.rect.x, pl.rect.y))
            if len(act) > 1:
                act = act[1]
                dx = clip_value(act[0] + 0.25 - self.rect.x, self.speed, -self.speed)
                dy = clip_value(act[1] + 0.25 - self.rect.y, self.speed, -self.speed)
                if not any_collisions(self, dx, 0):
                    self.rect.x += dx
                if not any_collisions(self, 0, dy):
                    self.rect.y += dy


class Skeleton(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.skeleton
        self.max_cooldown = 300
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.6 / FPS
        self.damage = -70 * difficulty
        self.max_health = 80 * difficulty
        self.health = self.max_health

    def update(self, cells):
        super().update(cells)
        can_see = True

        for x, y in unique_pairs():
            if cells[x][y].tile not in assets.NAME_BG:
                if pygame.Rect(x, y, 1, 1).clipline(
                        self.rect.centerx, self.rect.centery, pl.rect.centerx, pl.rect.centery):
                    can_see = False
                    break
        if can_see:
            if self.cooldown < all_time:
                arrow = Arrow(self.rect.centerx, self.rect.centery,
                              pl.rect.x - self.rect.x, pl.rect.y - self.rect.y,
                              -2000 * difficulty)
                for i in locations[(pl.lx, pl.ly)].enemies:
                    arrow.forbidden_damages.append(i.uid)
                projectiles.append(arrow)
                self.cooldown = all_time + self.max_cooldown + random.randrange(-100, 100)

        else:
            act = find_path(cells, (self.rect.x, self.rect.y), (pl.rect.x, pl.rect.y))
            if len(act):
                act = act[1]
                dx = clip_value(act[0] + 0.25 - self.rect.x, self.speed, -self.speed)
                dy = clip_value(act[1] + 0.25 - self.rect.x, self.speed, -self.speed)
                if not any_collisions(self, dx, 0):
                    self.rect.x += dx
                if not any_collisions(self, 0, dy):
                    self.rect.y += dy


class Spider(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.spider
        self.max_cooldown = 2000
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.8 / FPS
        self.damage = -3 * difficulty
        self.max_health = 450 * difficulty
        self.health = self.max_health

    def update(self, cells):
        super().update(cells)

        if self.cooldown < all_time:
            if (self.rect.x - pl.rect.x) ** 2 + (self.rect.y - pl.rect.y) ** 2 < enemy_radius ** 2:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage)
                pl.effects.append(Effect('health', 10000, -0.01 * difficulty, 300))
        if (self.rect.x - pl.rect.x) ** 2 + (self.rect.y - pl.rect.y) ** 2 >= enemy_radius ** 2:
            dx = clip_value(pl.rect.x - self.rect.x, self.speed, -self.speed)
            dy = clip_value(pl.rect.y - self.rect.y, self.speed, -self.speed)
            if not any_collisions(self, dx, 0, c=False):
                if not any_collisions(self, dx, 0, m=False):
                    self.rect.x += dx
                else:
                    self.rect.x += dx // 2
            if not any_collisions(self, 0, dy, c=False):
                if not any_collisions(self, 0, dy, m=False):
                    self.rect.y += dy
                else:
                    self.rect.y += dy // 2


class Mag(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.mag
        self.max_cooldown = random.randrange(2000, 3000)
        self.cooldown = 1000 + all_time
        self.speed = 1.1 / FPS
        self.damage = -100 * difficulty
        self.max_health = 125 * difficulty
        self.health = self.max_health

    def update(self, cells):
        super().update(cells)
        if self.cooldown < all_time:
            self.cooldown = all_time + self.max_cooldown + random.randrange(-1000, 500)
            multiplier = random.randrange(9, 12) / 10
            mag_circles.append(MagCircle(pl.rect.centerx, pl.rect.centery, self.damage * multiplier,
                                         0.5 * multiplier, 3000))


class MagCircle:
    def __init__(self, x, y, d, s, time_delta):
        self.x = x
        self.y = y
        self.s = s
        self.d = d
        self.detonation_time = time_delta + all_time

    def check(self):
        return self.detonation_time < all_time


class TempText:
    def __init__(self, x, y, text, text_color, r=20, text_size=30):
        self.x = x + random.randrange(-r, r)
        self.y = y + random.randrange(-r, r)
        self.font = pygame.font.Font(assets.PATH + 'font.ttf', text_size).render(text, True,
                                                                                 text_color)
        self.time = 0

    def get(self):
        return self.font

    def update(self):
        self.time += 1
        if self.time < FPS // 2:
            self.y -= 50 // FPS
        else:
            self.font.set_alpha(255 - (self.time - 499) // 2)
        if self.y < -50:
            temp_text.remove(self)


pygame.init()

debug = 0  # DEBUG!
FPS = 60

NAME_ENEMY = {'zombie': Zombie, 'skeleton': Skeleton, 'spider': Spider, 'mag': Mag}

PICK_PRIORITY = ['item_gold_heart', 'item_heart', 'item_healing_potion', 'item_arrow']
LOOT_LIST = ['item_healing_potion', 'item_arrow', 'item_gold_heart', 'item_heart']
DROP_AMOUNT = [(1, 4), (2, 6), (10, 20), (15, 30)]
DROP_CHANCES = {Skeleton: [0.1, 0.6, 0.05, 0.1],
                Zombie: [0.1, 0.2, 0.1, 0.3],
                Spider: [0.2, 0.0, 0.2, 0.7],
                Mag: [0.2, 0.1, 0.5, 0.05]}

difficulty = 1

monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]
DISPLAY_S = min(monitor_size)
display = pygame.display.set_mode(monitor_size)  # , pygame.FULLSCREEN)
clock = pygame.time.Clock()

PF_FINDER = AStarFinder(diagonal_movement=DiagonalMovement.always)

SPLASH_POTION_AMPLIFIER = 100

SWORD_DAMAGE = -50

ARROW_DEFAULT_COOLDOWN = 500
ARROW_MAX_COOLDOWN = -5000
SWORD_DEFAULT_COOLDOWN = 360

TT_COLOR = [(255, 70, 70), (255, 255, 70)]

fire_cooldown = ARROW_MAX_COOLDOWN
sword_cooldown = 0
sword_angle = 0
all_time = 0

size = 0
# будет определено в функции set_cell_size()
cell_s = 0
half = 0
quarter = 0
cell_ss = (0, 0)
half_d = (0, 0)
quarter_d = (0, 0)
arrow_size = (0, 0)
splash_potion_radius = 0
player_radius = 0
enemy_radius = 0
cam_dx = 0
cam_dy = 0

last_given_uid = -1
forbidden_damages = []

projectiles = []
temp_text = []
mag_circles = []
locations = dict()
locations_names = []

set_cell_size(70)
assets = Assets('assets2/')
pl = Player(0, 0)  # will be set in run_game()


def load_location(path, coord):
    x, y = coord
    with open(f'levels2/{path}/{x} {y}.txt') as fil:
        fil = fil.read().strip().split()

        cells = [[fil[x + y * size] for y in range(size)] for x in range(size)]
        enemies = []
        items = []

        fil = fil[size ** 2:]
        for i in range(int(fil[0])):
            tx, ty, n = fil[i + 1].split('-')
            enemies.append(NAME_ENEMY[n](float(tx), float(ty)))

        fil = fil[int(fil[0]) + 1:]
        for i in range(int(fil[0])):
            t = fil[i + 1].split('-')
            items.append(Item(float(t[0]), float(t[1]), t[2], int(t[3])))
    return Location(cells, enemies, items)


def load_level(path):
    global size, locations, locations_names, pl
    with open(f'levels2/{path}/start.txt') as file:
        file = [int(i) for i in file.read().strip().split()]
        size = file[0]

        pl = Player(file[1], file[2])
        locations_names = [(file[i], file[i + 1]) for i in range(3, len(file), 2)]
        locations = dict([(i, load_location(path, i)) for i in locations_names])


def run_game(path):
    global fire_cooldown, all_time, sword_angle, sword_cooldown, last_given_uid, size, locations
    shlopa_ending = False
    throwing_mode = False
    sword_uid = -1
    load_level(path)
    location = locations[(0, 0)]

    while pl.health > 0:
        time_d = clock.tick(FPS)
        sword_angle += time_d

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed(3)
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()

        if keys[pygame.K_f] and pl.potions:
            throwing_mode = True
            display_update(location)
            pygame.draw.circle(display, (200, 200, 200), (mouse_pos[0], mouse_pos[1]),
                               splash_potion_radius, 2)
            pygame.display.flip()
            continue

        elif throwing_mode:
            throwing_mode = False
            pl.potions -= 1

            for entity in location.enemies + [pl]:
                if collision_with_circle(entity, mouse_pos[0], mouse_pos[1],
                                         splash_potion_radius):
                    if type(entity) in {Skeleton, Zombie, Mag}:
                        entity.apply_damage(-SPLASH_POTION_AMPLIFIER)
                    else:
                        entity.apply_damage(SPLASH_POTION_AMPLIFIER)
                    if type(entity) == Player:
                        entity.effects = [i for i in entity.effects if i.amplifier > 0]

        fire_cooldown = max(ARROW_MAX_COOLDOWN, fire_cooldown - time_d)
        all_time += time_d

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                to_pick = [i for i in location.items if i.can_pick()]
                if len(to_pick):
                    t = min(to_pick, key=lambda x: PICK_PRIORITY.index(x.item))
                    t.pick()
                    location.items.remove(t)

        if mouse[0] and (fire_cooldown < 0) and pl.arrows:
            pl.arrows -= 1
            arrow = Arrow(pl.rect.x + quarter, pl.rect.y + quarter,
                          mouse_pos[0] - pl.rect.x * cell_s - quarter,
                          mouse_pos[1] - pl.rect.y * cell_s - quarter,
                          fire_cooldown)
            arrow.forbidden_damages.append(0)
            projectiles.append(arrow)

            fire_cooldown = ARROW_DEFAULT_COOLDOWN

        if mouse[2] and (fire_cooldown < 0):
            sword_angle = pygame.Vector2(
                pl.rect.centerx * cell_s - mouse_pos[0],
                pl.rect.centery * cell_s - mouse_pos[1]).as_polar()[1]
            sword_uid = get_uid()
            sword_cooldown = all_time + SWORD_DEFAULT_COOLDOWN
            fire_cooldown = SWORD_DEFAULT_COOLDOWN

        # player
        pl.update(location.cells)
        shlopa_ending = pl.health <= 0
        pl.check_damage_arrow()
        dlx, dly = pl.move(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        change = False
        if dlx and not location.enemies:
            if (pl.lx + dlx, pl.ly) in locations_names:
                pl.lx += dlx
                pl.rect.x = DISPLAY_S - half - pl.rect.x
                change = True
        if dly and not location.enemies:
            if (pl.lx, pl.ly + dly) in locations_names:
                pl.ly += dly
                pl.rect.y = DISPLAY_S - half - pl.rect.y
                change = True
        if change:
            location = locations[(pl.lx, pl.ly)]
            projectiles.clear()
            temp_text.clear()
            mag_circles.clear()
            continue

        # projectiles
        for i in projectiles:
            if i.update(location.cells):
                location = locations[(pl.lx, pl.ly)]

        # temporary text
        for i in temp_text:
            i.update(time_d)

        # mag circles
        for i in mag_circles:
            if i.check():
                if collision_with_circle(pl, i.x + quarter, i.y + quarter, i.s):
                    pl.apply_damage(i.d)
                mag_circles.remove(i)

        # enemies
        sword_line = pygame.Vector2()
        sword_line.from_polar((player_radius, sword_angle))
        for i in location.enemies:
            i.update(location.cells)
            i.check_damage_arrow()
            if sword_cooldown > all_time and ((sword_uid, i.uid) not in forbidden_damages):
                if i.rect.clipline(pl.rect.centerx, pl.rect.centery, pl.rect.centerx + sword_line.x,
                                   pl.rect.centery + sword_line.y):
                    forbidden_damages.append((sword_uid, i.uid))
                    i.apply_damage(SWORD_DAMAGE)

            if i.health <= 0:
                loot = DROP_CHANCES[type(i)]
                for d in enumerate(loot):
                    if random.random() < d[1]:
                        location.items.append(
                            Item(i.rect.x, i.rect.y, LOOT_LIST[d[0]],
                                 int(random.randrange(10, 30) // difficulty + 1)))
                location.enemies.remove(i)

        # effects
        for i in location.enemies + [pl]:
            for j in i.effects:
                if j.check():
                    i.effects.remove(j)

        display_update(location)
        pygame.display.flip()
    pygame.mixer.stop()
    pygame.mixer.Sound.play(assets.death_sound)
    timer = 0
    while timer < 8000:
        timer += clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
        display.blit(assets.death_screen, (0, 0))
        pygame.display.flip()
    if not pl.lx and not pl.ly and pl.rect.x == pl.rect.y == cell_s and shlopa_ending:
        pygame.mixer.Sound.play(assets.shlopa_sound)
        timer = 0
        while timer < 20000:
            timer += clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()
            display.blit(assets.shlopa_screen, (0, 0))
            pygame.display.flip()


def display_update(location: Location):
    display.fill((0, 0, 0))
    # bg
    location.bg_group.draw(display)

    # mag circles
    for i in mag_circles:
        pygame.draw.circle(display, (200, 30, 0), (i.x * cell_s, i.y * cell_s), i.s)

    # sword circle
    pygame.draw.circle(display, (100, 100, 100),
                       (pl.rect.x * cell_s + quarter, pl.rect.y + quarter),
                       player_radius, 2)

    # cells
    location.block_group.draw(display)

    # projectiles
    for i in projectiles:
        display.blit(i.image, ((i.x + i.image_dx) * cell_s,
                               (i.y + i.image_dy) * cell_s))

    # enemies and steve
    for i in location.enemies + [pl]:
        i.draw(display)
    for i in location.enemies + [pl]:
        i.draw_health(display)

    # template text
    for i in temp_text:
        display.blit(i.get(), (i.x, i.y))

    # items
    for i in location.items:
        i.draw(display)

    # sword
    if sword_cooldown > all_time:
        sword_line = pygame.Vector2()
        sword_line.from_polar((player_radius, sword_angle))
        pygame.draw.line(display, (255, 0, 0), (pl.rect.centerx, pl.rect.centery),
                         (pl.rect.centerx + sword_line.x, pl.rect.centery + sword_line.y),
                         4)

    # gui
    tx = cell_s + half + 10
    ty = 1
    th = quarter
    tw = cell_s + half

    if fire_cooldown > 0:
        pygame.draw.rect(display, (200, 200, 200), (tx, ty, tw, th))
        pygame.draw.rect(display, (100, 100, 100),
                         (tx, ty, tw - tw * fire_cooldown // ARROW_DEFAULT_COOLDOWN, quarter))
    elif fire_cooldown != ARROW_MAX_COOLDOWN:
        pygame.draw.rect(display, (100, 100, 100), (tx, ty, tw, th))
        pygame.draw.rect(display, (200, 0, 0),
                         (tx, ty, tw * fire_cooldown // ARROW_MAX_COOLDOWN, th))
    else:
        pygame.draw.rect(display, (255, 0, 0), (tx, ty, tw, th))
    if fire_cooldown <= 0:
        display.blit(get_text(str(count_damage(fire_cooldown))), (tx, ty))
    eff_number = 1
    for i in pl.effects:
        texture = ''
        if i.sort == 'health':
            if i.amplifier > 0:
                texture = assets.regeneration
            else:
                texture = assets.poison
        display.blit(texture, (DISPLAY_S - half * eff_number, 0))

    # arrows and potions
    pygame.draw.rect(display, (100, 100, 100), (0, 0, half * 3, half))
    display.blit(assets.item_arrow, (0, 0))
    display.blit(get_text(str(pl.arrows)), (0, 0))
    display.blit(assets.item_healing_potion, (cell_s, 0))
    display.blit(get_text(str(pl.potions)), (cell_s, 0))

    # can move
    if location.enemies:
        pygame.draw.line(display, (255, 10, 10), (0, cell_s),
                         (0, monitor_size[1] - cell_s), width=3)
        pygame.draw.line(display, (255, 10, 10), (monitor_size[0] - 1, cell_s),
                         (monitor_size[0] - 1, monitor_size[1] - cell_s), width=3)


def get_text(mess, font_color=(0, 0, 0), font_type=assets.PATH + 'font.ttf', font_size=15):
    return pygame.font.Font(font_type, font_size).render(mess, True, font_color)


def find_path(mat, start, end):
    (x1, y1), (x2, y2) = start, end
    mat = [[(1 if mat[i][j] in assets.NAME_BACKGROUND else 0)
            for i in range(size)] for j in range(size)]
    grid = Grid(matrix=mat)
    start = grid.node(int(x1), int(x2))
    end = grid.node(int(x2), int(y2))

    path, runs = PF_FINDER.find_path(start, end, grid)
    return path


def unique_pairs(a=size, b=size):
    for i in range(a):
        for j in range(b):
            yield i, j


def any_collisions(self, x, y, c=True, m=True):
    location = locations[(pl.lx, pl.ly)]
    cells = location.cells
    rect = self.rect.move(x, y)
    if c:
        for i, j in unique_pairs():
            if cells[i][j] in assets.NAME_HARD:
                if Rect(i, j, 1, 1).colliderect(rect):
                    return True
    if m:
        for i in (set(location.enemies) | {pl}) - {self}:
            if i.rect.colliderect(rect):
                return True
    return False


def collision_with_circle(i: Entity, x, y, r):
    return (i.rect.centerx - x) ** 2 + (i.rect.centery - y) ** 2 < (r + 0.25) ** 2


def count_damage(c):
    return int((c // -100) ** 1.5) + (20 if c == ARROW_MAX_COOLDOWN else 0)


def clip_value(v, ma, mi):
    return max(min(v, ma), mi)


run_game('test')
