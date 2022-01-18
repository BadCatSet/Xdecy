import os
from os.path import abspath

import pygame


def load_image(path, scale: tuple = None, colorkey: tuple[int, int, int] = None):
    try:
        image = pygame.image.load(path)
        if scale is not None:
            image = pygame.transform.scale(image, scale)
        if colorkey is not None:
            image.set_colorkey(colorkey)
        return image
    except FileNotFoundError:
        exit(f'Файл {path} не найден!')


class NewField:
    def __init__(self, monitor_size, path):
        self.path = path
        self.blocks_paths = dict()
        for i in range(9):
            self.blocks_paths[f'b{i}'] = load_image(
                f'{self.path}\\resourcepacks\\standard\\b{i}.png', (50, 50))
            if i < 3:
                self.blocks_paths[f'h{i}'] = load_image(
                    f'{self.path}\\resourcepacks\\standard\\h{i}.png', (50, 50))
        self.blocks_paths['s0'] = load_image(f'{self.path}\\resourcepacks\\standard\\s0.png',
                                             (50, 50))

        self.item_paths = dict()
        for i in filter(
                lambda x: x.startswith('item'),
                os.listdir(f"{self.path}\\resourcepacks\\standard\\")):
            self.item_paths[i] = load_image(
                f'{self.path}\\resourcepacks\\standard\\{i}', (50, 50), (255, 255, 255))

        self.item_map_paths = dict()
        for k, v in self.item_paths.items():
            v = pygame.transform.scale(v, (25, 25))
            v.set_colorkey((255, 255, 255))
            self.item_map_paths[k] = v

        self.mob_paths = dict()
        for i in ['zombie', 'skeleton', 'spider', 'mag']:
            self.mob_paths[i] = load_image(f'{self.path}\\resourcepacks\\standard\\{i}.png',
                                           (50, 50))

        self.mob_map_paths = dict()
        for k, v in self.mob_paths.items():
            v = pygame.transform.scale(v, (25, 25))
            v.set_colorkey((255, 255, 255))
            self.mob_map_paths[k] = v

        self.field = [['b0' for _ in range(15)] for _ in range(15)]
        self.items = set()
        self.mobs = set()
        self.x0, self.y0 = ((monitor_size[1] - 750) // 2), ((monitor_size[1] - 750) // 2)

    def draw(self, screen: pygame.Surface):
        for x, line in enumerate(self.field):
            for y, element in enumerate(line):
                screen.blit(self.blocks_paths.get(element, self.blocks_paths['b0']),
                            (y * 50 + self.x0, x * 50 + self.y0))
        for item in self.items:
            screen.blit(self.item_map_paths[item[0]],
                        (self.x0 + item[1] * 50, self.y0 + item[2] * 50))
        for mob in self.mobs:
            print(self.mob_map_paths, mob[0])
            screen.blit(self.mob_map_paths[mob[0]], (self.x0 + mob[1] * 50, self.y0 + mob[2] * 50))

    def get_rect(self):
        return self.x0, self.y0, 750, 750  # 750 - сторона квадрата поля

    def process_click(self, x, y, selected_block):
        self.field[y // 50][x // 50] = selected_block

    def save_level(self):
        with open(f'{self.path}\\saves\\created\\new_level.txt', mode='w', encoding='utf-8') as f:
            for line in self.field:
                f.write(f"{' '.join(line)}\n")
            f.write(f"{str(len(self.mobs))}\n")
            for mob in self.mobs:
                f.write(f'{mob[1]}-{mob[2]}-{mob[0]}\n')
            f.write(f"{str(len(self.items))}\n")
            for item in self.items:
                f.write(f'{item[1]}-{item[2]}-{item[0]}-45\n')


class BaseButton:
    def __init__(self, source: pygame.Surface, x: int, y: int):
        self.x, self.y = x, y
        self.source = source

    def draw(self, screen: pygame.Surface):
        screen.blit(self.source, (self.x, self.y))

    def set_coords(self, x: int, y: int):
        self.x, self.y = x, y

    def get_rect(self):
        return self.x, self.y, self.source.get_width(), self.source.get_height()


class TextButton(BaseButton):
    def __init__(self, text: str, x: int, y: int, font_size: int, color=(255, 0, 0),
                 background_color=(60, 60, 60)):
        self.font = pygame.font.Font(None, font_size)
        self.color, self.background_color = color, background_color
        self.text = text

        super().__init__(self.font.render(text, True, self.color), x, y)

    def set_coords(self, x: int, y: int):
        super().set_coords(x, y)
        self.source = self.font.render(self.text, True, self.color)


class ImageButton(BaseButton):
    red = pygame.Color('red')

    def __init__(self, source_on_tools: pygame.Surface, x: int, y: int, name: str):
        super().__init__(source_on_tools, x, y)
        self.name = name

    def drawTool(self, screen, selected_block):
        super().draw(screen)
        if selected_block == self.name:
            pygame.draw.rect(screen, self.red, self.get_rect(), 2)


def isCoordsInRect(coords: tuple[int, int], rect: tuple[int, int, int, int]):
    return coords[0] in range(rect[0], rect[0] + rect[2] + 1) and \
           coords[1] in range(rect[1], rect[1] + rect[3] + 1)


def main():
    pygame.init()
    monitor_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    path = '\\'.join(abspath(__file__).split('\\')[:-1])

    new_field = NewField(monitor_size, path)
    field_rect = new_field.get_rect()

    exitButton = TextButton("Выйти", monitor_size[0] - 100, 20, 30)
    saveButton = TextButton("Сохранить локацию", monitor_size[0] - 100, 40, 30)
    text_buttons = [exitButton, saveButton]
    for y0, text_button in enumerate(text_buttons):
        text_button.set_coords(
            monitor_size[0] - text_button.source.get_width() - 10,
            y0 * text_button.source.get_height() + 10)

    block_buttons = []
    for i, (name, block_path) in enumerate(new_field.blocks_paths.items()):
        block_buttons.append(
            ImageButton(block_path, field_rect[0] + field_rect[2] + 50, i * 60 + new_field.y0, name))
    selected_block = block_buttons[0].name

    item_buttons = []
    for i, (name, block_path) in enumerate(new_field.item_paths.items()):
        item_buttons.append(
            ImageButton(block_path, field_rect[0] + field_rect[2] + 125, i * 60 + new_field.y0,
                        name))
    selected_item = item_buttons[0].name

    mob_buttons = []
    for i, (name, block_path) in enumerate(new_field.mob_paths.items()):
        mob_buttons.append(
            ImageButton(block_path, field_rect[0] + field_rect[2] + 200, i * 60 + new_field.y0,
                        name))
    selected_mob = mob_buttons[0].name

    screen = pygame.display.set_mode(monitor_size)
    pygame.display.set_caption("Xdecy level editor")
    pygame.display.set_icon(load_image(f'{path}\\resourcepacks\\standard\\icon.ico'))
    clock = pygame.time.Clock()
    FPS = 60
    running = True

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if isCoordsInRect(event.pos, new_field.get_rect()):
                        new_field.process_click(
                            event.pos[0] - new_field.x0,
                            event.pos[1] - new_field.y0,
                            selected_block
                        )
                    for text_button in text_buttons:
                        if isCoordsInRect(event.pos, text_button.get_rect()):
                            if text_button == exitButton:
                                running = False
                            if text_button == saveButton:
                                new_field.save_level()
                    for block_button in block_buttons:
                        if isCoordsInRect(event.pos, block_button.get_rect()):
                            selected_block = block_button.name
                    for item_button in item_buttons:
                        if isCoordsInRect(event.pos, item_button.get_rect()):
                            selected_item = item_button.name
                    for mob_button in mob_buttons:
                        if isCoordsInRect(event.pos, mob_button.get_rect()):
                            selected_mob = mob_button.name
                if event.button == pygame.BUTTON_RIGHT:
                    if isCoordsInRect(event.pos, field_rect):
                        new_field.items.add((selected_item,
                                             ((event.pos[0] - field_rect[0]) // 25) / 2,
                                             ((event.pos[1] - field_rect[1]) // 25) / 2))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    pos = pygame.mouse.get_pos()
                    if isCoordsInRect(pos, field_rect):
                        new_field.mobs.add((selected_mob,
                                            ((pos[0] - field_rect[0]) // 25) / 2,
                                            ((pos[1] - field_rect[1]) // 25) / 2))

        screen.fill((0, 0, 0))
        new_field.draw(screen)
        [i.drawTool(screen, selected_block) for i in block_buttons]
        [i.drawTool(screen, selected_item) for i in item_buttons]
        [i.drawTool(screen, selected_mob) for i in mob_buttons]
        [i.draw(screen) for i in text_buttons]
        pygame.display.flip()


if __name__ == '__main__':
    main()
    pygame.quit()
