"""
v1.1
"""
tpath_load = False  # use alternative algorithm of pathfinding loader

import random
from math import sin

import pygame

if tpath_load:
    from tpath import AStarFinder, DiagonalMovement, Grid
else:
    from pathfinding.finder.a_star import AStarFinder
    from pathfinding.core.diagonal_movement import DiagonalMovement
    from pathfinding.core.grid import Grid


def get_uid():
    global last_given_uid
    last_given_uid += 1
    return last_given_uid


class Location:
    def __init__(self, cells, enemies, items):
        self.cells = cells
        self.enemies = enemies
        self.items = items

    def __setitem__(self, c, value):
        self.cells[c[0]][c[1]] = value

    def __getitem__(self, c):
        return self.cells[c[0]][c[1]]

    def __repr__(self):
        return str(self.cells) + '|' + str(self.enemies) + '|' + str(self.items)


class Arrow:
    def __init__(self, x, y, dx, dy, speed):

        self.x = x
        self.y = y
        self.d = pygame.Vector2(dx, dy).normalize() * (speed // -300 + 2)
        self.angle = self.d.as_polar()[1]

        self.uid = get_uid()

        self.texture = pygame.transform.rotate(assets['arrow'], -self.angle)
        self.texture.set_colorkey((255, 255, 255))

        rrr = self.texture.get_rect()
        tv = pygame.Vector2()
        tv.from_polar((arrow_size[0] // 2, self.angle - 5))
        self.texture_dx = - rrr.centerx - tv.x
        self.texture_dy = - rrr.centery - tv.y

        self.damage = -count_damage(speed)

    def update(self, cells):
        self.x += self.d.x
        self.y += self.d.y

        if not (0 <= self.x <= DISPLAY_S and 0 <= self.y <= DISPLAY_S):
            projectiles.remove(self)
            return

        tx, ty = int(self.x // cell_s), int(self.y // cell_s)
        if 0 <= tx < len(cells) and 0 <= ty < len(cells):
            if cells[tx][ty] in NAME_SOFT:
                projectiles.remove(self)
                locations[(pl.lx, pl.ly)][tx, ty] = random.choices(NAME_BG, weights=FREQUENCY_BG)[0]
                return True
            if cells[tx][ty] in NAME_HARD:
                projectiles.remove(self)


class Item:
    def __init__(self, x, y, item, amount):
        self.x = x
        self.y = y
        self.start_time = all_time + random.randrange(-1000, 1000)
        self.texture = assets[item]
        self.dx = self.texture.get_rect().centerx
        self.dy = self.texture.get_rect().centery

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
                TempText(pl.r.x + quarter, pl.r.y + quarter, str(delta), (225, 215, 0)))
        if self.item == 'item_heart':
            pl.apply_damage(self.amount)

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
    def __init__(self, x, y, texture):
        self.r = pygame.Rect(x, y, half, half)
        self.texture = texture

        self.health = None
        self.max_health = None
        self.effects = []
        self.speed = 0

        self.uid = get_uid()

    def apply_damage(self, delta):
        global temp_text
        delta = min(self.health + delta, self.max_health) - self.health
        self.health += delta
        if int(delta) < 0:
            pygame.mixer.Sound.play(assets['hit'])
        if int(delta):
            temp_text.append(TempText(self.r.centerx, self.r.centery, str(int(delta)),
                                      TT_COLOR[1 if self.uid else 0]))

    def check_damage_arrow(self):
        global forbidden_damages
        for i in projectiles:
            if self.r.collidepoint(i.x, i.y):
                if (i.uid, self.uid) not in forbidden_damages:
                    forbidden_damages.append((i.uid, self.uid))
                    if self.health > 0:
                        self.apply_damage(i.damage)
                        if self.health <= 0:
                            projectiles.remove(i)

    def update(self, cells):
        for i in self.effects:
            t = i.get()
            if t[0] == 'health':
                self.apply_damage(t[1])

    def __repr__(self):
        return type(self).__name__ + '(' + str(self.r.x) + ', ' + str(self.r.y) + ')'


class Player(Entity):
    def __init__(self, x, y, lx, ly):
        super().__init__(x, y, assets['steve'])
        self.lx = lx
        self.ly = ly
        self.health = 200
        self.max_health = self.health
        self.speed = 6
        self.potions = 0
        self.arrows = 0

    def move(self, dx, dy):
        dx = dx * self.speed
        dy = dy * self.speed
        dlx, dly = 0, 0
        if 0 <= self.r.x + dx <= DISPLAY_S - half:
            if not any_collisions(self, dx, 0):
                self.r.x += dx
            elif not any_collisions(self, dx // abs(dx), 0):
                self.r.x += dx // abs(dx)
        else:
            dlx = -1 if self.r.x + dx < 0 else 1

        if 0 <= self.r.y + dy <= DISPLAY_S - half:
            if not any_collisions(self, 0, dy):
                self.r.y += dy
            elif not any_collisions(self, 0, dy // abs(dy)):
                self.r.y += dy // abs(dy)
        else:
            dly = -1 if self.r.y + dy < 0 else 1
        return dlx, dly


class Zombie(Entity):
    def __init__(self, x, y, texture):
        super().__init__(x, y, texture)
        self.max_cooldown = 500
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 2
        self.damage = -random.randrange(7, 20) * difficulty
        self.health = random.randrange(450, 550) * difficulty
        self.max_health = self.health

    def update(self, cells):
        super().update(cells)

        if self.cooldown < all_time:
            if ((self.r.x - pl.r.x) ** 2 + (self.r.y - pl.r.y) ** 2) < enemy_radius ** 2:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage + random.randrange(-5, 9))

        if (pl.r.x - self.r.x) ** 2 + (pl.r.y - self.r.y) ** 2 >= cell_s ** 2:

            act = find_path(cells, (self.r.x // cell_s, self.r.y // cell_s),
                            (pl.r.x // cell_s, pl.r.y // cell_s,))
            if len(act) > 1:
                act = act[1]
                dx = max(min(act[0] * cell_s + quarter - self.r.x, 2 * difficulty),
                         -2 * difficulty)
                dy = max(min(act[1] * cell_s + quarter - self.r.y, 2 * difficulty),
                         -2 * difficulty)
                if not any_collisions(self, dx, 0):
                    self.r.x += dx
                if not any_collisions(self, 0, dy):
                    self.r.y += dy


class Skeleton(Entity):
    def __init__(self, x, y, texture):
        super().__init__(x, y, texture)
        self.max_cooldown = 300
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 2
        self.damage = -random.randrange(50, 100) * difficulty
        self.health = random.randrange(50, 120) * difficulty
        self.max_health = self.health

    def update(self, cells):
        super().update(cells)
        can_see = True

        for x, y in unique_pairs():
            if cells[x][y] not in NAME_BG:
                if pygame.Rect(x * cell_s, y * cell_s, cell_s, cell_s).clipline(
                        self.r.x + quarter, self.r.y + quarter, pl.r.x + quarter, pl.r.y + quarter):
                    can_see = False
                    break
        if can_see:
            if self.cooldown < all_time:
                projectiles.append(Arrow(self.r.x + quarter, self.r.y + quarter,
                                         pl.r.x - self.r.x, pl.r.y - self.r.y, -2000 * difficulty))
                self.cooldown = all_time + self.max_cooldown + random.randrange(-100, 100)
                for i in locations[(pl.lx, pl.ly)].enemies:
                    forbidden_damages.append((last_given_uid, i.uid))
        else:
            act = find_path(cells, (self.r.x // cell_s, self.r.y // cell_s),
                            (pl.r.x // cell_s, pl.r.y // cell_s,))
            if len(act) != 0:
                act = act[1]
                dx = max(min(act[0] * cell_s + quarter - self.r.x, self.speed * difficulty),
                         -self.speed * difficulty)
                dy = max(min(act[1] * cell_s + quarter - self.r.y, self.speed * difficulty),
                         -self.speed * difficulty)
                if not any_collisions(self, dx, 0):
                    self.r.x += dx
                if not any_collisions(self, 0, dy):
                    self.r.y += dy


class Spider(Entity):
    def __init__(self, x, y, texture):
        super().__init__(x, y, texture)
        self.max_cooldown = 2000
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 2
        self.damage = -random.randrange(2, 3) * difficulty
        self.health = random.randrange(400, 500) * difficulty
        self.max_health = self.health

    def update(self, cells):
        super().update(cells)

        if self.cooldown < all_time:
            if ((self.r.x - pl.r.x) ** 2 + (self.r.y - pl.r.y) ** 2) < enemy_radius ** 2:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage + random.randrange(-1, 2))
                pl.effects.append(Effect('health', 10000, -0.01 * difficulty, 300))
        if ((self.r.x - pl.r.x) ** 2 + (self.r.y - pl.r.y) ** 2) >= enemy_radius ** 2:
            dx = max(min(pl.r.x - self.r.x, 2 * difficulty), -2 * difficulty)
            dy = max(min(pl.r.y - self.r.y, 2 * difficulty), -2 * difficulty)
            if not any_collisions(self, dx, 0, c=False):
                if not any_collisions(self, dx, 0, m=False):
                    self.r.x += dx
                else:
                    self.r.x += dx // 2
            if not any_collisions(self, 0, dy, c=False):
                if not any_collisions(self, 0, dy, m=False):
                    self.r.y += dy
                else:
                    self.r.y += dy // 2


class Mag(Entity):
    def __init__(self, x, y, texture):
        super().__init__(x, y, texture)
        self.max_cooldown = random.randrange(2000, 3000)
        self.cooldown = 1000 + all_time
        self.speed = 2
        self.damage = -random.randrange(90, 120) * difficulty
        self.health = random.randrange(100, 150) * difficulty
        self.max_health = self.health

    def update(self, cells):
        super().update(cells)
        if self.cooldown < all_time:
            self.cooldown = all_time + self.max_cooldown + random.randrange(-1000, 500)
            multiplier = random.randrange(9, 12) / 10
            mag_circles.append(MagCircle(pl.r.centerx, pl.r.centery, self.damage * multiplier,
                                         half * multiplier, 3000))


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
        self.font = pygame.font.Font(directory + 'font.ttf', text_size).render(
            text, True, text_color)
        self.time = 0

    def get(self):
        return self.font

    def update(self, time):
        self.time += time
        if self.time < 500:
            self.y -= 50 // time
        else:
            self.font.set_alpha(255 - (self.time - 499) // 2)
        if self.y < -50:
            temp_text.remove(self)


PF_FINDER = AStarFinder(diagonal_movement=DiagonalMovement.always)

debug = 0  # DEBUG!

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
                Mag: [0.2, 0.1, 0.5, 0.05]}

FREQUENCY_BG = [400, 1, 1, 1, 1, 1, 1, 1]
NAME_ENEMY = {'zombie': Zombie, 'skeleton': Skeleton, 'spider': Spider, 'mag': Mag}

NAME_DISPLAY_S = ['death screen', 'shlopa screen']
NAME_BG = ['bg0', 'bg1', 'bg2', 'bg3', 'bg4', 'bg5', 'bg6', 'bg7']
NAME_HARD = ['1', '2', '3', '5']
NAME_SOFT = ['5']
NAME_MOB_S = ['steve', 'zombie', 'skeleton', 'spider', 'mag', 'poison', 'regeneration',
              'item_healing_potion',
              'item_arrow']
NAME_QUARTER_S = ['item_gold_heart', 'item_heart']
NAME_ARROW = 'arrow'

NAME_SOUNDS = ['death sound', 'hit', 'shlopa sound']

level = 'test'
directory = 'assets/'
difficulty = 1

fire_cooldown = ARROW_MAX_COOLDOWN
sword_cooldown = 0
sword_angle = 0
all_time = 0

last_given_uid = -1
forbidden_damages = []

projectiles = []
temp_text = []
mag_circles = []

shlopa_ending = False

pygame.init()
monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]
pygame.display.set_caption('Xdecy')
pygame.display.set_icon(pygame.image.load(directory + 'icon.ico'))

clock = pygame.time.Clock()


def load_location(coord):
    x, y = coord
    cells = [['' for _ in range(size)] for _ in range(size)]
    enemies = []
    items = []
    with open(f'levels/{level}/{x} {y}.txt') as fil:
        fil = fil.read().strip().split()
        for i in range(size):
            for j in range(size):
                r = fil[i + j * size]
                if r == '0':
                    cells[i][j] = random.choices(NAME_BG, weights=FREQUENCY_BG)[0]
                else:
                    cells[i][j] = r

        fil = fil[size ** 2:]
        for i in range(int(fil[0])):
            tx, ty, n = fil[i + 1].split('-')
            enemies.append(NAME_ENEMY[n](int(tx) * cell_s, int(ty) * cell_s, assets[n]))

        fil = fil[int(fil[0]) + 1:]
        for i in range(int(fil[0])):
            t = fil[i + 1].split('-')
            items.append(Item(float(t[0]) * cell_s, float(t[1]) * cell_s, t[2], int(t[3])))

    return Location(cells, enemies, items)


with open(f'levels/{level}/start.txt') as file:
    file = [int(i) for i in file.read().strip().split()]
    size = file[0]

    DISPLAY_S = min(monitor_size)
    cell_s = DISPLAY_S // size
    half = cell_s // 2
    quarter = cell_s // 4

    DISPLAY_S = size * cell_s
    blit_wd = (max(monitor_size) - DISPLAY_S) // 2

    player_radius = cell_s * 1.25
    splash_potion_radius = cell_s * 1.2
    enemy_radius = cell_s

    arrow_size = (cell_s, cell_s * 3 // 8)

    assets = {i: pygame.mixer.Sound(directory + i + '.wav') for i in NAME_SOUNDS}

    assets.update(
        {i: pygame.transform.scale(pygame.image.load(directory + i + '.png'), (cell_s, cell_s))
         for i in (NAME_BG + NAME_HARD + NAME_SOFT)})

    assets.update(
        {i: pygame.transform.scale(pygame.image.load(directory + i + '.png'), (half, half))
         for i in NAME_MOB_S})

    assets.update(
        {i: pygame.transform.scale(pygame.image.load(directory + i + '.png'), (quarter, quarter))
         for i in NAME_QUARTER_S})

    assets.update({i: pygame.transform.scale(pygame.image.load(directory + i + '.png'),
                                             (DISPLAY_S, DISPLAY_S))
                   for i in NAME_DISPLAY_S})

    assets[NAME_ARROW] = pygame.transform.scale(pygame.image.load(directory + NAME_ARROW + '.png'),
                                                arrow_size)

    assets['item_arrow'].set_colorkey((255, 255, 255))
    assets['item_gold_heart'].set_colorkey((255, 255, 255))
    assets['item_heart'].set_colorkey((255, 255, 255))

    pl = Player(file[4] * cell_s, file[3] * cell_s, file[1], file[2])
    locations_names = [(file[i], file[i + 1]) for i in range(5, len(file), 2)]
    locations = dict([(i, load_location(i)) for i in locations_names])

    display = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)


def run_game():
    global pl, fire_cooldown, all_time, shlopa_ending, sword_angle, sword_cooldown, last_given_uid
    location = locations[(pl.lx, pl.ly)]
    throwing_mode = False
    sword_uid = -1

    while pl.health > 0:
        time_d = clock.tick(60)
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
                if collision_with_circle(entity, mouse_pos[0] - blit_wd, mouse_pos[1],
                                         splash_potion_radius):
                    if type(entity) in {Skeleton, Zombie, Mag}:
                        entity.apply_damage(-SPLASH_POTION_AMPLIFIER)
                    if type(entity) == Spider:
                        entity.apply_damage(SPLASH_POTION_AMPLIFIER)
                    if type(entity) == Player:
                        entity.effects = [i for i in entity.effects if i.amplifier > 0]
                        entity.apply_damage(SPLASH_POTION_AMPLIFIER)

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
            projectiles.append(Arrow(pl.r.x + quarter, pl.r.y + quarter,
                                     mouse_pos[0] - pl.r.x - quarter - blit_wd,
                                     mouse_pos[1] - pl.r.y - quarter,
                                     fire_cooldown))
            forbidden_damages.append((last_given_uid, 0))
            fire_cooldown = ARROW_DEFAULT_COOLDOWN

        if mouse[2] and (fire_cooldown < 0):
            sword_angle = pygame.Vector2(pl.r.centerx - mouse_pos[0] - blit_wd,
                                         pl.r.centery - mouse_pos[1]).as_polar()[1]
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
                pl.r.x = DISPLAY_S - half - pl.r.x
                change = True
        if dly and not location.enemies:
            if (pl.lx, pl.ly + dly) in locations_names:
                pl.ly += dly
                pl.r.y = DISPLAY_S - half - pl.r.y
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
                if i.r.clipline(pl.r.centerx, pl.r.centery, pl.r.centerx + sword_line.x,
                                pl.r.centery + sword_line.y):
                    forbidden_damages.append((sword_uid, i.uid))
                    i.apply_damage(SWORD_DAMAGE)

            if i.health <= 0:
                loot = DROP_CHANCES[type(i)]
                for d in enumerate(loot):
                    if random.random() < d[1]:
                        location.items.append(
                            Item(i.r.x, i.r.y, LOOT_LIST[d[0]],
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
    pygame.mixer.Sound.play(assets['death sound'])
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
        display.blit(assets['death screen'], (blit_wd, 0))
        pygame.display.flip()
    if not pl.lx and not pl.ly and pl.r.x == pl.r.y == cell_s and shlopa_ending:
        pygame.mixer.Sound.play(assets['shlopa sound'])
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
            display.blit(assets['shlopa screen'], (blit_wd, 0))
            pygame.display.flip()


def display_update(location):
    display.fill((0, 0, 0))
    # bg
    for x, y in unique_pairs():
        if location[x, y] in NAME_BG:
            display.blit(assets[location[x, y]], (x * cell_s + blit_wd, y * cell_s))
    # mag circles
    for i in mag_circles:
        pygame.draw.circle(display, (200, 30, 0), (i.x + blit_wd, i.y), i.s)

    # sword circle
    pygame.draw.circle(display, (100, 100, 100), (pl.r.x + quarter + blit_wd, pl.r.y + quarter),
                       player_radius, 2)

    # cells
    for x, y in unique_pairs():
        if location[x, y] not in NAME_BG:
            display.blit(assets[location[x, y]], (x * cell_s + blit_wd, y * cell_s))

    # projectiles
    for i in projectiles:
        display.blit(i.texture, (i.x + i.texture_dx + blit_wd, i.y + i.texture_dy))

    # enemies and steve
    for i in location.enemies + [pl]:
        display.blit(i.texture, i.r.move((blit_wd, 0)))
    for i in location.enemies + [pl]:
        pygame.draw.rect(display, (100, 100, 100), (i.r.x + blit_wd, i.r.y - 10, half, 5))
        pygame.draw.rect(display, (255, 0, 0),
                         (i.r.x + blit_wd, i.r.y - 10, half * i.health // i.max_health, 5))
        display.blit(get_text(str(int(i.health))), (i.r.x + blit_wd, i.r.y - 15))

    # template text
    for i in temp_text:
        display.blit(i.get(), (i.x + blit_wd, i.y))

    # items
    for i in location.items:
        offset = sin((all_time + i.start_time) / 300) * 10
        display.blit(i.texture, (i.x + blit_wd, i.y + offset))
        display.blit(get_text(str(i.amount)), (i.x + blit_wd, i.y + offset))

    # sword
    if sword_cooldown > all_time:
        sword_line = pygame.Vector2()
        sword_line.from_polar((player_radius, sword_angle))
        pygame.draw.line(display, (255, 0, 0), (pl.r.centerx + blit_wd, pl.r.centery),
                         (pl.r.centerx + sword_line.x + blit_wd, pl.r.centery + sword_line.y), 4)

    # gui
    tx = cell_s + half + 10
    ty = 1
    th = quarter
    tw = cell_s + half

    if fire_cooldown > 0:
        pygame.draw.rect(display, (200, 200, 200), (tx + blit_wd, ty, tw, th))
        pygame.draw.rect(display, (100, 100, 100),
                         (tx + blit_wd, ty, tw - tw * fire_cooldown // ARROW_DEFAULT_COOLDOWN,
                          quarter))
    elif fire_cooldown != ARROW_MAX_COOLDOWN:
        pygame.draw.rect(display, (100, 100, 100), (tx + blit_wd, ty, tw, th))
        pygame.draw.rect(display, (200, 0, 0),
                         (tx + blit_wd, ty, tw * fire_cooldown // ARROW_MAX_COOLDOWN, th))
    else:
        pygame.draw.rect(display, (255, 0, 0), (tx + blit_wd, ty, tw, th))
    if fire_cooldown <= 0:
        display.blit(get_text(str(count_damage(fire_cooldown))), (tx + blit_wd, ty))
    eff_number = 1
    for i in pl.effects:
        texture = ''
        if i.sort == 'health':
            if i.amplifier > 0:
                texture = assets['regeneration']
            else:
                texture = assets['poison']
        display.blit(texture, (DISPLAY_S - half * eff_number + blit_wd, 0))

    # arrows and potions
    pygame.draw.rect(display, (100, 100, 100), (blit_wd, 0, half * 3, half))
    display.blit(assets['item_arrow'], (blit_wd, 0))
    display.blit(get_text(str(pl.arrows)), (blit_wd, 0))
    display.blit(assets['item_healing_potion'], (half * 2 + blit_wd, 0))
    display.blit(get_text(str(pl.potions)), (half * 2 + blit_wd, 0))

    # can move
    if location.enemies:
        pygame.draw.line(display, (255, 10, 10), (blit_wd, cell_s), (blit_wd, DISPLAY_S - cell_s),
                         width=3)
        pygame.draw.line(display, (255, 10, 10), (DISPLAY_S - 1 + blit_wd, cell_s),
                         (DISPLAY_S - 1 + blit_wd, DISPLAY_S - cell_s), width=3)
    pygame.draw.rect(display, (0, 0, 0), (0, 0, blit_wd, monitor_size[1]))
    pygame.draw.rect(display, (0, 0, 0), (blit_wd + DISPLAY_S, 0, blit_wd, monitor_size[1]))


def get_text(mess, font_color=(0, 0, 0), font_type=directory + 'font.ttf', font_size=15):
    return pygame.font.Font(font_type, font_size).render(mess, True, font_color)


def find_path(mat, start, end):
    mat = [[(1 if mat[i][j] in NAME_BG else 0) for i in range(len(mat))] for j in range(len(mat))]
    grid = Grid(matrix=mat)
    start = grid.node(*start)
    end = grid.node(*end)

    path, runs = PF_FINDER.find_path(start, end, grid)
    return path


def unique_pairs(a=size, b=size):
    for i in range(a):
        for j in range(b):
            yield i, j


def any_collisions(self, x, y, c=True, m=True):
    location = locations[(pl.lx, pl.ly)]
    cells = location.cells
    rect = self.r.move(x, y)
    if c:
        for i, j in unique_pairs():
            if cells[i][j] in NAME_HARD:
                if pygame.Rect(i * cell_s, j * cell_s, cell_s, cell_s).colliderect(rect):
                    return True
    if m:
        for i in (set(location.enemies) | {pl}) - {self}:
            if i.r.colliderect(rect):
                return True
    return False


def collision_with_circle(i: Entity, x, y, r):
    return (i.r.centerx - x) ** 2 + (i.r.centery - y) ** 2 < (r + quarter) ** 2


def count_damage(c):
    return int((c // -100) ** 1.5) + (20 if c == ARROW_MAX_COOLDOWN else 0)


run_game()
