import os

import pygame
from pygame.transform import scale as pg_scale
import pygame_menu

from levelEditor import main


class ToStartMenu(Exception):
    pass


class Assets:
    PATH = ''
    NAME_BACKGROUND = ['b0']
    NAME_HARD = ['h0', 'h1', 'h2']
    NAME_SOFT = ['s0']
    NAME_HALF_S = ['steve', 'zombie', 'skeleton', 'spider', 'mag', 'poison', 'regeneration',
                   'item_healing_potion', 'item_arrow']
    NAME_QUARTER_S = ['item_gold_heart', 'item_heart']
    NAME_ARROW = 'arrow'

    def __init__(self, path, cell_s):
        half = cell_s // 2
        quarter = cell_s // 4

        self.cell_s = cell_s
        self.half = half
        self.quarter = quarter

        path = 'resourcepacks/' + path
        self.PATH = path
        for i in self.NAME_BACKGROUND + self.NAME_HARD + self.NAME_SOFT:
            self.load_image(i, (cell_s, cell_s))

        for i in self.NAME_HALF_S:
            self.load_image(i, (half, half))

        for i in self.NAME_QUARTER_S:
            self.load_image(i, (quarter, quarter))

        self.item_arrow.set_colorkey((255, 255, 255))
        self.item_gold_heart.set_colorkey((255, 255, 255))
        self.item_heart.set_colorkey((255, 255, 255))
        self.item_healing_potion.set_colorkey((255, 255, 255))

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
        return self.NAME_BACKGROUND[0]


def terminate():
    pygame.quit()
    exit()


def run_editor(path):
    print('editor started with path: %s' % path)
    menu_display = pygame.Surface((400, monitor_size[1])).convert()
    menu = pygame_menu.menu.Menu(title='',
                                 width=400, height=monitor_size[1])
    menu.add.button(title='1')
    menu.add.image(assets.PATH + 'b0.png')
    while True:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise ToStartMenu
        menu.update(events)

        display.fill((0, 0, 0))
        menu.draw(menu_display)
        display.blit(menu_display, (0, 0))
        pygame.display.flip()


def run_menu_start():
    def start_editor():
        path = 'saves/' + level_selector.get_value()[0][0] + '/'
        try:
            run_editor(path)
        except ToStartMenu:
            pass

    def start_menu_new_level():
        try:
            run_menu_new_level()
        except ToStartMenu:
            pass

    level_names = []
    for i in os.listdir('./saves'):
        if os.path.isdir('./saves/' + i):
            level_names.append(i)
    menu = pygame_menu.menu.Menu(title='editor',
                                 width=monitor_size[0], height=monitor_size[1],
                                 theme=theme)
    menu.add.button(title='edit',
                    action=start_editor)
    level_selector = menu.add.dropselect(title='level: ',
                                         items=list(zip(level_names, level_names)),
                                         placeholder_add_to_selection_box=False)
    menu.add.label(title='')
    menu.add.button(title='new level',
                    action=start_menu_new_level)
    menu.add.button(title='quit',
                    action=terminate)
    level_selector.set_value(level_names[0])
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
        pygame.display.flip()


def run_menu_new_level():
    def create():
        main(level_name.get_value())
        raise ToStartMenu

    def back():
        raise ToStartMenu

    menu = pygame_menu.menu.Menu(title='create ner level',
                                 width=monitor_size[0], height=monitor_size[1],
                                 theme=theme)
    level_name = menu.add.text_input(title='title: ',
                                     default='')
    menu.add.button(title='create',
                    action=create)
    menu.add.button(title='back',
                    action=back)
    while True:
        clock.tick(FPS)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                back()
        menu.draw(display)
        menu.update(events)
        pygame.display.flip()


pygame.init()
monitor_size = pygame.display.Info().current_w, pygame.display.Info().current_h
display = pygame.display.set_mode(monitor_size)
clock = pygame.time.Clock()
FPS = 60

theme = pygame_menu.themes.THEME_BLUE.copy()
theme.title_bar_style = pygame_menu.themes.MENUBAR_STYLE_SIMPLE
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

assets = Assets('standard/', 70)

if __name__ == "__main__":
    run_menu_start()
