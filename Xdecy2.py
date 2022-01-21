"""
v2.-1
"""

from math import sin
import os
import random

# use normal way to load pathfinding
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
# use alternative way to load pathfinding
# from tpath import AStarFinder, DiagonalMovement, Grid
import pygame
from pygame import Rect as pgRect, Surface, Vector2
from pygame.transform import rotate as pg_rotate, scale as pg_scale
from pygame_colliders import create_collider
import pygame_menu
import pyrect


class GameOverSignal(Exception):
    pass


class ExitGameSignal(Exception):
    pass


class RetrySignal(Exception):
    pass


class ReturnToMenuSignal(Exception):
    pass


class Rect(pyrect.Rect):
    x: int
    y: int
    w: int
    h: int

    def clipline(self, point1, point2):
        (x1, y1), (x2, y2) = point1, point2
        pg_rect = pgRect(self.x * cell_s, self.y * cell_s, self.w * cell_s, self.h * cell_s)
        return bool(pg_rect.clipline(x1 * cell_s, y1 * cell_s, x2 * cell_s, y2 * cell_s))


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
        path = 'resourcepacks/' + path
        self.PATH = path
        for i in self.NAME_BACKGROUND + self.NAME_HARD + self.NAME_SOFT:
            self.load_image(i, (cell_s, cell_s))

        for i in self.NAME_HALF_S:
            self.load_image(i, (half, half))

        for i in self.NAME_QUARTER_S:
            self.load_image(i, (quarter, quarter))
        for i in self.NAME_MONITOR_S:
            self.load_image(i, monitor_size)

        self.load_image(self.NAME_ARROW, arrow_size)
        self.item_arrow.set_colorkey((255, 255, 255))
        self.item_gold_heart.set_colorkey((255, 255, 255))
        self.item_heart.set_colorkey((255, 255, 255))
        self.item_healing_potion.set_colorkey((255, 255, 255))

        for i in self.NAME_SOUNDS:
            sound = pygame.mixer.Sound(path + i + '.wav')
            self.__setattr__(i, sound)

    def load_image(self, name, im_size=None, colorkey=None, filetype='.png'):
        fullname = os.path.join(self.PATH, name + filetype)
        if not os.path.isfile(fullname):
            print(f"Файл с изображением '{fullname}' не найден")
            terminate()

        image = pygame.image.load(fullname)
        if im_size is not None:
            image = pg_scale(image, im_size)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((1, 1))
            image.set_colorkey(colorkey)
        self.__setattr__(name, image.convert_alpha())

    def get_bg(self):
        return random.choices(self.NAME_BACKGROUND, weights=self.FREQUENCY_BG, k=1)[0]


class MyGroup(pygame.sprite.Group):
    def draw(self, surface: Surface):
        for i in self.sprites():
            i.draw(surface)


class MySprite(pygame.sprite.Sprite):
    def draw(self, surface: Surface):
        pass


class Cell(MySprite):
    def __init__(self, x, y, tile, owner):
        if tile == 'b0':
            super().__init__(owner.bg_group)
            tile = assets.get_bg()
        else:
            super().__init__(owner.block_group)

        self.tile = tile
        self.rect = Rect(x, y, 1, 1)
        self.image = eval(f'assets.{tile}')

    def draw(self, surface: Surface):
        coord = self.rect.x * cell_s + cam_dx, self.rect.y * cell_s + cam_dy
        surface.blit(self.image, coord)


class Location:
    def __init__(self, cells, enemies, items):
        self.bg_group = MyGroup()
        self.block_group = MyGroup()  # hard and soft
        self.cells = [[Cell(x, y, cells[x][y], self) for y in range(size)] for x in range(size)]
        self.enemies = enemies
        self.items = items

    def make_bg(self, x, y):
        self.cells[x][y].kill()
        self.cells[x][y] = Cell(x, y, 'b0', self)

    def __getitem__(self, coord):
        x, y = coord
        return self.cells[x][y]

    def __repr__(self):
        return self.__dict__


class Arrow:
    def __init__(self, coords, dx, dy, tension):
        self.x, self.y = coords

        self.d = Vector2(dx, dy).normalize() * interpolate(tension, 0, 2000, 0.2, 0.5)
        self.angle = self.d.as_polar()[1]

        self.image = pygame.transform.rotate(assets.arrow, -self.angle)
        self.image.set_colorkey((255, 255, 255))

        im_dx, im_dy = self.image.get_rect().center
        tv = Vector2()
        tv.from_polar((arrow_size[0] // 2, self.angle - 5))
        self.image_dx = - im_dx - tv.x
        self.image_dy = - im_dy - tv.y

        self.damage = -count_damage(tension)

        self.forbidden_damages = []

    def update(self):
        cells = location.cells
        self.x += self.d.x
        self.y += self.d.y

        if not (0 <= self.x <= size and 0 <= self.y <= size):
            projectiles.remove(self)
            return

        tx, ty = int(self.x), int(self.y)

        if cells[tx][ty].tile in assets.NAME_SOFT:
            location.make_bg(tx, ty)
            projectiles.remove(self)
            return
        if cells[tx][ty].tile in assets.NAME_HARD:
            projectiles.remove(self)

    def draw(self, surface: Surface):
        # pygame.draw.circle(surface, (255, 0, 0), (self.x * cell_s, self.y * cell_s), 10)
        coord = self.x * cell_s + self.image_dx + cam_dx, self.y * cell_s + self.image_dy + cam_dy
        surface.blit(self.image, coord)


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
        return collision_with_circle(pl, self.x, self.y, pl.RADIUS)

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

    def draw(self, surface: Surface):
        offset = sin((all_time + self.start_time) / 300) * 10
        coord = self.x * cell_s - self.dx + cam_dx, self.y * cell_s - self.dy + offset + cam_dy
        surface.blit(self.image, coord)
        surface.blit(get_text(str(self.amount)), coord)

    def __repr__(self):
        return f"{type(self).__name__}({self.x}, {self.y}, '{self.item}', {self.amount})"


class Effect:
    def __init__(self, sort, time, amplifier, cooldown):
        self.time_to_del = all_time + time
        self.sort = sort
        self.amplifier = amplifier
        self.cooldown = all_time
        self.max_cooldown = cooldown
        if sort == 'health':
            if amplifier > 0:
                self.image = assets.regeneration
            else:
                self.image = assets.poison

    def get(self):
        if self.cooldown < all_time:
            self.cooldown += self.max_cooldown
            if self.sort == 'health':
                return 'health', self.amplifier * (self.cooldown - all_time)
        return 'health', 0

    def check(self):
        return self.time_to_del < all_time

    def draw(self, surface: Surface, n):
        surface.blit(self.image, (monitor_size[0] - half * n + cam_dx, cam_dy))


class Entity:
    HEALTH_TEXT_COLOR = 255, 70, 70
    RADIUS = 0

    def __init__(self, x, y):
        self.rect = Rect(x, y, 0.5, 0.5, enableFloat=True)
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
            temp_text.append(TempText(self.rect.centerx * cell_s, self.rect.centery * cell_s,
                                      str(int(delta)), self.HEALTH_TEXT_COLOR))

    def check_damage_arrow(self):
        for i in projectiles:
            if self.rect.collide((i.x, i.y)):
                if self.uid not in i.forbidden_damages:
                    i.forbidden_damages.append(self.uid)
                    self.apply_damage(i.damage)
                    if self.health <= 0:
                        projectiles.remove(i)

    def update(self):
        for i in self.effects:
            t = i.get()
            if t[0] == 'health':
                self.apply_damage(t[1])

    def draw(self, surface: Surface):
        surface.blit(self.image, (self.rect.x * cell_s + cam_dx, self.rect.y * cell_s + cam_dy))

    def draw_health(self, surface: Surface):
        pygame.draw.rect(surface, (100, 100, 100), (self.rect.x * cell_s + cam_dx,
                                                    self.rect.y * cell_s - 10 + cam_dy, half, 5))
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x * cell_s + cam_dx,
                                                self.rect.y * cell_s - 10 + cam_dy,
                                                half * self.health // self.max_health, 5))
        surface.blit(get_text(str(int(self.health))),
                     (self.rect.x * cell_s + cam_dx, self.rect.y * cell_s - 15 + cam_dy))

    def __repr__(self):
        return self.__dict__


class Enemy(Entity):
    DROP_CHANCES = {}
    HEALTH_TEXT_COLOR = 255, 255, 70
    RADIUS = 1

    def check_death(self):
        global score
        if self.health > 0:
            return
        for loot, poss in self.DROP_CHANCES.items():
            if random.random() < poss:
                location.items.append(Item(self.rect.centerx, self.rect.centery, loot,
                                           random.randrange(*DROP_AMOUNT[loot])))
        score += 1
        location.enemies.remove(self)
        for i in locations.values():
            if i.enemies:
                break
        else:
            raise GameOverSignal('win')


class Player(Entity):
    RADIUS = 1.25

    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.steve
        self.lx = 0
        self.ly = 0
        self.max_health = 200
        self.health = self.max_health
        self.speed = 4 / FPS
        self.potions = 0
        self.arrows = 0

    def move(self, kw, ka, ks, kd):
        dx, dy = (kd - ka) * self.speed, (ks - kw) * self.speed  # здесь всё правильно
        if self.rect.x + dx < 0:
            dlx = -1
        elif self.rect.x + dx > size - 0.5:
            dlx = 1
        else:
            dlx = 0
            if can_move(self, dx, 0, mode='cm'):
                self.rect.x += dx
            elif can_move(self, sign(dx), 0, mode='cm'):
                self.rect.x += sign(dx)

        if self.rect.y + dy < 0:
            dly = -1
        elif self.rect.y + dy > size - 0.5:
            dly = 1
        else:
            dly = 0
            if can_move(self, 0, dy, mode='cm'):
                self.rect.y += dy
            elif can_move(self, 0, sign(dy), mode='cm'):
                self.rect.y += sign(dy)
        return dlx, dly


class Zombie(Enemy):
    DROP_CHANCES = {'item_healing_potion': 0.1, 'item_arrow': 0.2, 'item_gold_heart': 0.1,
                    'item_heart': 0.3}

    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.zombie
        self.max_cooldown = 500
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.8 / FPS
        self.damage = -11 * difficulty
        self.max_health = 500 * difficulty
        self.health = self.max_health

    def update(self):
        super().update()
        cells = location.cells
        if self.cooldown < all_time:
            if (self.rect.x - pl.rect.x) ** 2 + (self.rect.y - pl.rect.y) ** 2 < self.RADIUS ** 2:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage + random.randrange(-5, 9))

        if (pl.rect.x - self.rect.x) ** 2 + (pl.rect.y - self.rect.y) ** 2 >= 1:
            act = find_path(cells, *self.rect.center, *pl.rect.center)
            if len(act) >= 2:
                act = act[1]
                dx = trim_value(act[0] + 0.25 - self.rect.x, self.speed, -self.speed)
                dy = trim_value(act[1] + 0.25 - self.rect.x, self.speed, -self.speed)
                if can_move(self, dx, 0, mode='cmb'):
                    self.rect.x += dx
                if can_move(self, 0, dy, mode='cmb'):
                    self.rect.y += dy


class Skeleton(Enemy):
    DROP_CHANCES = {'item_healing_potion': 0.1, 'item_arrow': 0.6, 'item_gold_heart': 0.05,
                    'item_heart': 0.1}

    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.skeleton
        self.max_cooldown = 300
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.6 / FPS
        self.tension = 500 * difficulty
        self.max_health = 80 * difficulty
        self.health = self.max_health

    def update(self):
        super().update()
        cells = location.cells
        can_see = True

        for x, y in unique_pairs(size, size):
            if cells[x][y].tile in assets.NAME_HARD:
                if Rect(x, y, 1, 1).clipline(self.rect.center, pl.rect.center):
                    can_see = False
                    break
        if can_see:
            if self.cooldown < all_time:
                arrow = Arrow(self.rect.center,
                              pl.rect.x - self.rect.x, pl.rect.y - self.rect.y,
                              self.tension)
                for i in locations[(pl.lx, pl.ly)].enemies:
                    arrow.forbidden_damages.append(i.uid)
                projectiles.append(arrow)
                self.cooldown = all_time + self.max_cooldown + random.randrange(-100, 100)

        else:
            act = find_path(cells, *self.rect.center, *pl.rect.center)
            if len(act) >= 2:
                act = act[1]
                dx = trim_value(act[0] + 0.25 - self.rect.x, self.speed, -self.speed)
                dy = trim_value(act[1] + 0.25 - self.rect.x, self.speed, -self.speed)
                if can_move(self, dx, 0, mode='cmb'):
                    self.rect.x += dx
                if can_move(self, 0, dy, mode='cmb'):
                    self.rect.y += dy


class Spider(Enemy):
    DROP_CHANCES = {'item_healing_potion': 0.2, 'item_arrow': 0.0, 'item_gold_heart': 0.2,
                    'item_heart': 0.7}

    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.spider
        self.max_cooldown = 2000
        self.cooldown = random.randrange(0, self.max_cooldown)
        self.speed = 0.8 / FPS
        self.damage = -3 * difficulty
        self.max_health = 450 * difficulty
        self.health = self.max_health

    def update(self):
        super().update()
        if (self.rect.x - pl.rect.x) ** 2 + (self.rect.y - pl.rect.y) ** 2 < self.RADIUS ** 2:
            if self.cooldown < all_time:
                self.cooldown = all_time + self.max_cooldown + random.randrange(-400, 500)
                pl.apply_damage(self.damage)
                pl.effects.append(Effect('health', 10000, -0.01 * difficulty, 300))
        else:
            dx = trim_value(pl.rect.x - self.rect.x, self.speed, -self.speed)
            dy = trim_value(pl.rect.y - self.rect.y, self.speed, -self.speed)

            if can_move(self, dx, 0, mode='cmb'):
                self.rect.x += dx
            elif can_move(self, dx / 2, 0, mode='mb'):
                self.rect.x += dx / 2
            if can_move(self, 0, dy, mode='cmb'):
                self.rect.y += dy
            elif can_move(self, 0, dy / 2, mode='mb'):
                self.rect.y += dy / 2


class Mag(Enemy):
    DROP_CHANCES = {'item_healing_potion': 0.2, 'item_arrow': 0.1, 'item_gold_heart': 0.5,
                    'item_heart': 0.05}

    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = assets.mag
        self.cooldown = 1000 + all_time
        self.speed = 1.1 / FPS
        self.damage = -100 * difficulty
        self.max_health = 125 * difficulty
        self.health = self.max_health

    def update(self):
        super().update()
        if self.cooldown < all_time:
            self.cooldown = all_time + self.max_cooldown()
            multiplier = random.randrange(9, 12) / 10
            mag_circles.append(MagCircle(*pl.rect.center, self.damage * multiplier,
                                         0.5 * multiplier, self.get_detonation_time()))

    @staticmethod
    def max_cooldown():
        return random.randrange(2000, 3000)

    @staticmethod
    def get_detonation_time():
        return random.randrange(700, 1000)


class MagCircle:
    def __init__(self, x, y, d, s, time_delta):
        self.x = x
        self.y = y
        self.s = s
        self.d = d
        self.start_time = all_time
        self.end_time = all_time + time_delta

    def update(self):
        if self.end_time < all_time:
            if collision_with_circle(pl, self.x + 0.25, self.y + 0.25, self.s):
                pl.apply_damage(self.d)
            mag_circles.remove(self)

    def draw(self, surface: Surface):
        pygame.draw.circle(surface, (200, 30, 0),
                           (self.x * cell_s + cam_dx, self.y * cell_s + cam_dy),
                           self.s * cell_s)
        pygame.draw.circle(surface, (255, 100, 0),
                           (self.x * cell_s + cam_dx, self.y * cell_s + cam_dy),
                           self.s * cell_s * interpolate(all_time,
                                                         self.start_time, self.end_time,
                                                         0, 1))


class TempText:
    def __init__(self, x, y, text, text_color, r=20, text_size=30):
        self.x = x + random.randrange(-r, r)
        self.y = y + random.randrange(-r, r)
        self.text = pygame.font.Font(assets.PATH + 'font.ttf', text_size).render(text, True,
                                                                                 text_color)
        self.start_time = all_time

    def update(self):
        time = all_time - self.start_time
        if time < FPS:
            self.y -= 70 / FPS
        elif time < FPS * 2:
            self.text.set_alpha(255 - (time - FPS) // 2)
        else:
            temp_text.remove(self)

    def draw(self, surface: Surface):
        surface.blit(self.text, (self.x + cam_dx, self.y + cam_dy))


class Weapon:
    def on_tick(self, is_pressed, time_d):
        pass

    def draw(self, surface: Surface):
        pass


class Sword(Weapon):
    DEFAULT_COOLDOWN = 500
    ATTACK_TIME = 150
    DAMAGE = -50
    v1 = Vector2(2, -0.25) / 4
    v2 = Vector2(6, -0.5) / 4
    v3 = Vector2(6, 0.5) / 4
    v4 = Vector2(2, 0.25) / 4

    def __init__(self):
        self.last_use = -10000
        self.area = []
        self.base_angle = 0
        self.forbidden_damages = []

    # noinspection PyUnusedLocal
    def on_tick(self, is_pressed, time_d):
        if all_time - self.last_use > self.DEFAULT_COOLDOWN and is_pressed:
            self.forbidden_damages = []
            self.last_use = all_time
            self.base_angle = Vector2(
                mouse_pos[0] - pl.rect.centerx * cell_s - cam_dx,
                mouse_pos[1] - pl.rect.centery * cell_s - cam_dy).as_polar()[1]
        if all_time - self.last_use < self.ATTACK_TIME:
            angle = self.base_angle + interpolate(all_time - self.last_use,
                                                  0, self.ATTACK_TIME, -23, 23)
            dxy = pl.rect.center
            v1 = self.v1.rotate(angle).xy + dxy
            v2 = self.v2.rotate(angle).xy + dxy
            v3 = self.v3.rotate(angle).xy + dxy
            v4 = self.v4.rotate(angle).xy + dxy

            area = (v1, v2, v3, v4)
            self.area = area
            # noinspection PyTypeChecker
            collider = create_collider(area)
            for i in location.enemies:
                if i in self.forbidden_damages:
                    continue
                area2 = (i.rect.topright, i.rect.topleft, i.rect.bottomleft, i.rect.bottomright)
                # noinspection PyTypeChecker
                collider2 = create_collider(area2)
                if collider.collide(collider2):
                    self.forbidden_damages.append(i)
                    i.apply_damage(self.DAMAGE)

    def draw(self, surface):
        if all_time - self.last_use > self.ATTACK_TIME:
            return

        area = [(x * cell_s + cam_dx, y * cell_s + cam_dy) for x, y in self.area]
        pygame.draw.polygon(surface, (255, 255, 255), area, 0)


class Bow(Weapon):
    MAX_TENSION = 2000

    def __init__(self):
        self.tension = 0

    def on_tick(self, is_pressed, time_d):
        if pl.arrows <= 0:
            return
        if is_pressed:
            self.tension = trim_value(self.tension + time_d, self.MAX_TENSION, 0)
        elif self.tension:
            pl.arrows -= 1
            arrow = Arrow(pl.rect.center,
                          mouse_pos[0] - pl.rect.centerx * cell_s - cam_dx,
                          mouse_pos[1] - pl.rect.centery * cell_s - cam_dy,
                          self.tension)
            arrow.forbidden_damages.append(pl.uid)
            projectiles.append(arrow)
            self.tension = 0

    def draw(self, surface: Surface):
        tx = cell_s + half + 10
        ty = 1
        th = quarter
        tw = cell_s + half
        if self.tension == self.MAX_TENSION:
            pygame.draw.rect(surface, (255, 0, 0), (tx, ty, tw, th))
        else:
            pygame.draw.rect(surface, mix_color((255, 100, 100), (0, 255, 0),
                                                self.tension / self.MAX_TENSION),
                             (tx, ty, tw * self.tension // self.MAX_TENSION, th))
        if self.tension:
            surface.blit(get_text(str(count_damage(self.tension))), (tx, ty))


class Potions(Weapon):
    DAMAGE = 100
    RADIUS = 1.2

    def __init__(self):
        self.was_pressed = False

    def on_tick(self, is_pressed, time_d):
        if not is_pressed and self.was_pressed and pl.potions > 0:
            pl.potions -= 1

            for entity in location.enemies + [pl]:
                if collision_with_circle(entity, (mouse_pos[0] - cam_dx) // cell_s,
                                         (mouse_pos[1] - cam_dy) // cell_s,
                                         self.RADIUS):
                    if type(entity) in {Skeleton, Zombie, Mag}:
                        entity.apply_damage(-self.DAMAGE)
                    else:
                        entity.apply_damage(self.DAMAGE)
                    if entity is pl:
                        entity.effects = [i for i in entity.effects if i.amplifier > 0]
        self.was_pressed = is_pressed

    def draw(self, surface: Surface):
        if self.was_pressed:
            pygame.draw.circle(surface, (200, 200, 200), (mouse_pos[0], mouse_pos[1]),
                               self.RADIUS * cell_s, 2)


def get_uid():
    global last_given_uid
    last_given_uid += 1
    return last_given_uid


def terminate():
    pygame.quit()
    exit()


def load_location(path, coord):
    x, y = coord
    with open(f'saves/{path}/{x} {y}.txt') as file:
        file = file.read().strip().split()

        cells = [[file[x + y * size] for y in range(size)] for x in range(size)]
        enemies = []
        items = []

        file = file[size ** 2:]
        for i in range(int(file[0])):
            tx, ty, n = file[i + 1].split('-')
            enemies.append(NAME_ENEMY[n](float(tx), float(ty)))

        file = file[int(file[0]) + 1:]
        for i in range(int(file[0])):
            t = file[i + 1].split('-')
            items.append(Item(float(t[0]), float(t[1]), t[2], int(t[3])))
    return Location(cells, enemies, items)


def load_level(path):
    global size, locations, locations_names, pl
    with open(f'saves/{path}/start.txt') as file:
        file = [int(i) for i in file.read().strip().split()]
        size = file[0]

        pl = Player(file[1], file[2])
        locations_names = [(file[i], file[i + 1]) for i in range(3, len(file), 2)]
        locations = dict([(i, load_location(path, i)) for i in locations_names])


def run_game(path):
    global all_time, size, locations, location, score, mouse_pos
    score = 0
    shlopa_ending = False

    load_level(path)
    location = locations[(0, 0)]

    while pl.health > 0:
        time_d = clock.tick(FPS)
        all_time += time_d

        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed(3)
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise ExitGameSignal
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                to_pick = [i for i in location.items if i.can_pick()]
                if len(to_pick):
                    t = min(to_pick, key=lambda x: PICK_PRIORITY.index(x.item))
                    t.pick()
                    location.items.remove(t)

        bow.on_tick(mouse[0], time_d)
        sword.on_tick(mouse[2], time_d)
        potions.on_tick(keys[pygame.K_f], time_d)

        # player
        pl.update()
        shlopa_ending = pl.health <= 0
        pl.check_damage_arrow()
        dlx, dly = pl.move(keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d])
        change = False
        if dlx and not location.enemies:
            if (pl.lx + dlx, pl.ly) in locations_names:
                pl.lx += dlx
                pl.rect.x = size - pl.rect.right
                change = True
        if dly and not location.enemies:
            if (pl.lx, pl.ly + dly) in locations_names:
                pl.ly += dly
                pl.rect.y = size - pl.rect.bottom
                change = True
        if change:
            location = locations[(pl.lx, pl.ly)]
            projectiles.clear()
            temp_text.clear()
            mag_circles.clear()
            continue

        # projectiles
        for i in projectiles:
            i.update()

        # temporary text
        for i in temp_text:
            i.update()

        # mag circles
        for i in mag_circles:
            i.update()

        # enemies
        for i in location.enemies:
            i.update()
            i.check_damage_arrow()
            i.check_death()

        # delete effects
        for i in location.enemies + [pl]:
            for j in i.effects:
                if j.check():
                    i.effects.remove(j)

        display_update()
        pygame.display.flip()
    pygame.mixer.stop()
    pygame.mixer.Sound.play(assets.death_sound)
    timer = 0
    while timer < 8000:
        timer += clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                break
        display.blit(assets.death_screen, (0, 0))
        pygame.display.flip()
    if pl.lx == pl.ly == 0 and pl.rect.x == pl.rect.y == 1 and shlopa_ending:
        pygame.mixer.Sound.play(assets.shlopa_sound)
        timer = 0
        while timer < 20000:
            timer += clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    break
            display.blit(assets.shlopa_screen, (0, 0))
            pygame.display.flip()
    raise GameOverSignal('loose')


def display_update():
    global cam_dx, cam_dy
    plx, ply = pl.rect.centerx * cell_s, pl.rect.centery * cell_s
    if size * cell_s < monitor_size[0]:
        cam_dx = monitor_size[0] // 2 - size * cell_s // 2
    else:
        cam_dx = trim_value(monitor_size[0] // 2 - plx,
                            0,
                            monitor_size[0] - size * cell_s)

    if size * cell_s < monitor_size[1]:
        cam_dy = monitor_size[1] // 2 - size * cell_s // 2
    else:
        cam_dy = trim_value(monitor_size[1] // 2 - ply,
                            0,
                            monitor_size[1] - size * cell_s)

    display.fill((0, 0, 0))
    # bg
    location.bg_group.draw(display)

    # mag circles
    for i in mag_circles:
        i.draw(display)

    # cells
    location.block_group.draw(display)

    # projectiles
    for i in projectiles:
        i.draw(display)

    # enemies and steve
    for i in location.enemies + [pl]:
        i.draw(display)
    for i in location.enemies + [pl]:
        i.draw_health(display)

    # template text
    for i in temp_text:
        i.draw(display)

    # items
    for i in location.items:
        i.draw(display)

    # weapons
    sword.draw(display)
    bow.draw(display)
    potions.draw(display)
    # gui

    for n, i in enumerate(pl.effects):
        i.draw(display, n)
    # arrows and potions
    pygame.draw.rect(display, (100, 100, 100), (0, 0, half * 3, half))
    display.blit(assets.item_arrow, (0, 0))
    display.blit(get_text(str(pl.arrows)), (0, 0))
    display.blit(assets.item_healing_potion, (cell_s, 0))
    display.blit(get_text(str(pl.potions)), (cell_s, 0))

    # can move
    if location.enemies:
        pygame.draw.line(display, (255, 10, 10), (0, 100),
                         (0, monitor_size[1] - 100), width=3)
        pygame.draw.line(display, (255, 10, 10), (monitor_size[0] - 1, 100),
                         (monitor_size[0] - 1, monitor_size[1] - 100), width=3)


def run_menu():
    level_names = []
    for i in os.listdir('./saves'):
        if os.path.isdir('./saves/' + i):
            level_names.append(i)
    assets_names = []
    for i in os.listdir('./resourcepacks'):
        if os.path.isdir('./resourcepacks/' + i):
            assets_names.append(i)

    l_length = max(map(lambda x: len(x), level_names))
    for i in range(len(level_names)):
        level_names[i] = (level_names[i].ljust(l_length, ' '), level_names[i])

    t_length = max(map(lambda x: len(x), assets_names))
    for i in range(len(assets_names)):
        assets_names[i] = (assets_names[i].ljust(t_length, ' '), assets_names[i])

    def change_assets(*_, **__):
        global assets
        assets = Assets(sr.get_value()[0][1] + '/')

    def start_game():
        try:
            values = sl.get_value()
            run_game(values[0][1])
        except ExitGameSignal:
            return False
        except GameOverSignal as e:
            try:
                if str(e) == 'loose':
                    run_menu_game_over()
                if str(e) == 'win':
                    run_menu_game_win()
            except ReturnToMenuSignal:
                return False
            except RetrySignal:
                return True

    def start_game_core():
        while start_game():
            pass

    menu = pygame_menu.Menu(title='Xdecy2',
                            width=monitor_size[0], height=monitor_size[1],
                            theme=theme)
    menu.add.button('START GAME', start_game_core)

    sr = menu.add.selector(title='RESOURCEPACK: ',
                           items=assets_names,
                           onchange=change_assets)

    sl = menu.add.selector(title='LEVEL: ',
                           items=level_names)
    menu.add.button('QUIT', pygame_menu.events.EXIT)
    sr.set_value('standard'.ljust(t_length, ' '))
    sl.set_value('test'.ljust(l_length, ' '))
    while True:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                terminate()
        menu.draw(display)
        menu.update(events)
        # noinspection PyUnboundLocalVariable
        ba = pg_rotate(pg_scale(assets.b3.convert_alpha(), (150, 150)), 45)
        bb = pg_rotate(pg_scale(assets.b4.convert_alpha(), (130, 130)), -45)
        bc = pg_rotate(pg_scale(assets.b7.convert_alpha(), (130, 130)), 45)
        bd = pg_rotate(pg_scale(assets.b8.convert_alpha(), (150, 150)), -45)

        display.blit(ba, (210, 210))
        display.blit(bb, (monitor_size[0] - 300, 130))
        display.blit(bc, (100, monitor_size[1] - 300))
        display.blit(bd, (monitor_size[0] - 400, monitor_size[1] - 370))

        pygame.display.flip()


def run_menu_game_over():
    def retry():
        raise RetrySignal

    def return_to_menu():
        raise ReturnToMenuSignal

    menu = pygame_menu.Menu(title='..GAME OVER..',
                            width=monitor_size[0], height=monitor_size[1],
                            theme=game_over_theme)
    menu.add.label(title=f'SCORE: {score}')
    menu.add.button(title='RETRY', action=retry)
    menu.add.button(title='RETURN TO MENU', action=return_to_menu)

    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise ReturnToMenuSignal
        menu.draw(display)
        menu.update(events)
        pygame.display.flip()


def run_menu_game_win():
    def retry():
        raise RetrySignal

    def return_to_menu():
        raise ReturnToMenuSignal

    menu = pygame_menu.Menu(title='YOU WIN',
                            width=monitor_size[0], height=monitor_size[1],
                            theme=game_over_theme)
    menu.add.label(title=f'SCORE: {score}')
    menu.add.button(title='RETRY', action=retry)
    menu.add.button(title='RETURN TO MENU', action=return_to_menu)

    while True:
        clock.tick(FPS)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise ReturnToMenuSignal
        menu.draw(display)
        menu.update(events)
        pygame.display.flip()


# noinspection PyUnboundLocalVariable
def get_text(mess, font_color=(0, 0, 0), font_type=None, font_size=15):
    if font_type is None:
        font_type = assets.PATH + 'font.ttf'
    return pygame.font.Font(font_type, font_size).render(mess, True, font_color)


def find_path(mat, x1, y1, x2, y2, iq=False):
    if not iq:
        return [(x2, y2), (x2, y2), (x2, y2)]
    mat = [[(1 if mat[i][j].tile in assets.NAME_BACKGROUND else 0)
            for i in range(size)] for j in range(size)]
    grid = Grid(size, size, mat)
    start = grid.node(int(x1), int(y1))
    end = grid.node(int(x2), int(y2))

    path, runs = PF_FINDER.find_path(start, end, grid)
    return path


def unique_pairs(r_x, r_y):
    for x in range(r_x):
        for y in range(r_y):
            yield x, y


def can_move(self, dx, dy, mode='cm'):
    rect = Rect(self.rect.x + dx, self.rect.y + dy, 0.5, 0.5, enableFloat=True)

    if 'c' in mode:
        mx, my = int(rect.x), int(rect.y)
        for dx, dy in unique_pairs(2, 2):
            x, y = mx + dx, my + dy
            if x < 0 or x > size - 1 or y < 0 or y > size - 1:
                continue
            if location[x, y].tile not in assets.NAME_BACKGROUND:
                if Rect(x, y, 1, 1).collide(rect):
                    return False
    if 'm' in mode:
        for i in location.enemies + [pl]:
            if i == self:
                continue
            if i.rect.collide(rect):
                return False

    if 'b' in mode:
        if rect.left < 0 or rect.right > size - 1 or rect.top < 0 or rect.bottom > size - 1:
            return False
    return True


def collision_with_circle(i: Entity, x, y, r):
    return (i.rect.centerx - x) ** 2 + (i.rect.centery - y) ** 2 < (r + 0.25) ** 2


def trim_value(v, ma, mi):
    if v < mi:
        return mi
    if v > ma:
        return ma
    return v


def mix_color(c1, c2, a):
    b = 1 - a
    return c1[0] * a + c2[0] * b, c1[1] * a + c2[1] * b, c1[2] * a + c2[2] * b


'''
def intersect_ranges(*ranges):
    res = ranges[0]
    for i in ranges[1:]:
        res = (max(res[0], i[0]), min(res[1], i[1]))
        if res[0] > res[1]:
            return False
    return True
'''


def sign(v):
    if v < 0:
        return -1
    if v > 0:
        return 1
    return 0


def count_damage(tension):
    a = int(tension ** 1.5) // 223 - (0 if tension == bow.MAX_TENSION else 20)
    return trim_value(a, 399, 10)


def interpolate(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


pygame.init()

debug = 0  # DEBUG!
FPS = 60

NAME_ENEMY = {'zombie': Zombie, 'skeleton': Skeleton, 'spider': Spider, 'mag': Mag}

LOOT_LIST = ['item_healing_potion', 'item_arrow', 'item_gold_heart', 'item_heart']  # unused
PICK_PRIORITY = ['item_gold_heart', 'item_heart', 'item_healing_potion', 'item_arrow']
DROP_AMOUNT = {'item_healing_potion': (1, 4), 'item_arrow': (2, 6), 'item_gold_heart': (10, 20),
               'item_heart': (15, 30)}

difficulty = 1

monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h]
DISPLAY_S = min(monitor_size)
display = pygame.display.set_mode(monitor_size)

clock = pygame.time.Clock()

PF_FINDER = AStarFinder(diagonal_movement=DiagonalMovement.always)

all_time = 0
mouse_pos = (0, 0)
score = 0

size = 0

cell_s = 100
half = cell_s / 2
quarter = cell_s / 4

arrow_size = (cell_s, cell_s * 3 // 8)
cam_dx = 0
cam_dy = 0

last_given_uid = -1
forbidden_damages = []

projectiles = []
temp_text = []
mag_circles = []
locations = dict()
locations_names = []

assets = Assets('standard/')

# will be set in run_game()
pl = Player(0, 0)
sword = Sword()
bow = Bow()
potions = Potions()
location = Location([], [], [])

theme = pygame_menu.themes.THEME_BLUE.copy()
theme.title_background_color = 50, 50, 50
theme.title_font_color = 255, 20, 19
theme.title_font_shadow = False
theme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD

theme.widget_font_size = 40
theme.background_color = 33, 33, 33
theme.widget_font_color = 20, 255, 236
theme.selection_color = 255, 236, 20
theme.widget_selection_effect = pygame_menu.widgets.selection.LeftArrowSelection()
theme.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD

game_over_theme = theme.copy()
game_over_theme.title_bar_style = pygame_menu.themes.MENUBAR_STYLE_SIMPLE

run_menu()
