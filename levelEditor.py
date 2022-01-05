from os.path import abspath
from pprint import pprint

import pygame


def load_image(path, scale: tuple = None):
    try:
        image = pygame.image.load(path)
        if scale is not None:
            image = pygame.transform.scale(image, scale)
        return image
    except FileNotFoundError:
        exit(f'Файл {path} не найден!')


class NewField:
    def __init__(self, monitor_size, path):
        self.path = path
        self.blocks_paths = {'b0': load_image(f'{self.path}\\assets2\\b0.png', (50, 50)),
                             'b1': load_image(f'{self.path}\\assets2\\b1.png', (50, 50)),
                             'b2': load_image(f'{self.path}\\assets2\\b2.png', (50, 50)),
                             'b3': load_image(f'{self.path}\\assets2\\b3.png', (50, 50)),
                             'b4': load_image(f'{self.path}\\assets2\\b4.png', (50, 50)),
                             'b5': load_image(f'{self.path}\\assets2\\b5.png', (50, 50)),
                             'b6': load_image(f'{self.path}\\assets2\\b6.png', (50, 50)),
                             'b7': load_image(f'{self.path}\\assets2\\b7.png', (50, 50)),
                             'b8': load_image(f'{self.path}\\assets2\\b8.png', (50, 50))}
        self.field = [['b0' for _ in range(15)] for _ in range(15)]
        self.x0, self.y0 = ((monitor_size[1] - 750) // 2), ((monitor_size[1] - 750) // 2)

    def draw(self, screen: pygame.Surface):
        for x, line in enumerate(self.field):
            for y, element in enumerate(line):
                screen.blit(self.blocks_paths.get(element, self.blocks_paths['b0']),
                            (y * 50 + self.x0, x * 50 + self.y0))

    def get_rect(self):
        """
        return: (x, y, width, height)
        """
        return self.x0, self.y0, 750, 750  # 750 - сторона квадрата поля

    def process_click(self, x, y, selected_block):
        self.field[y // 50][x // 50] = selected_block

    def save_level(self):
        # for line in self.field:
        #     print(' '.join(line))
        # print('-' * 44)
        with open(f'{self.path}\\levels2\\created\\new_level.txt', mode='w', encoding='utf-8') as f:
            for line in self.field:
                f.write(f"{' '.join(line)}\n")


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
    def __init__(self, text: str, x: int, y: int, font_size: int, color=(255, 0, 0), background_color=(60, 60, 60)):
        self.font = pygame.font.Font(None, font_size)
        self.color, self.background_color = color, background_color
        self.text = text

        super().__init__(self.font.render(text, True, self.color), x, y)

    def set_coords(self, x: int, y: int):
        super().set_coords(x, y)
        self.source = self.font.render(self.text, True, self.color)


class BlockButton(BaseButton):
    red = pygame.Color('red')

    def __init__(self, source: pygame.Surface, x: int, y: int, name: str):
        super().__init__(source, x, y)
        self.name = name

    def drawBlock(self, screen, selected_block):
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
    exitButton = TextButton("Выйти", monitor_size[0] - 100, 20, 30)
    saveButton = TextButton("Сохранить локацию", monitor_size[0] - 100, 40, 30)
    text_buttons = [exitButton, saveButton]
    for y0, text_button in enumerate(text_buttons):
        text_button.set_coords(monitor_size[0] - text_button.source.get_width() - 10,
                               y0 * text_button.source.get_height() + 10)

    block_buttons = []
    field_rect = new_field.get_rect()
    for i, (name, block_path) in enumerate(new_field.blocks_paths.items()):
        block_buttons.append(BlockButton(block_path, field_rect[0] + field_rect[2] + 50, i * 60 + new_field.y0, name))

    screen = pygame.display.set_mode(monitor_size)
    pygame.display.set_caption("Xdecy level editor")
    pygame.display.set_icon(load_image(f'{path}\\assets2\\icon.ico'))

    selected_block = "b1"

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
                        new_field.process_click(event.pos[0] - new_field.x0, event.pos[1] - new_field.y0,
                                                selected_block)
                    for text_button in text_buttons:
                        if isCoordsInRect(event.pos, text_button.get_rect()):
                            if text_button == exitButton:
                                running = False
                            if text_button == saveButton:
                                new_field.save_level()
                    for block_button in block_buttons:
                        if isCoordsInRect(event.pos, block_button.get_rect()):
                            selected_block = block_button.name

        screen.fill((0, 0, 0))
        new_field.draw(screen)
        [i.drawBlock(screen, selected_block) for i in block_buttons]
        [i.draw(screen) for i in text_buttons]
        pygame.display.flip()


if __name__ == '__main__':
    main()
    pygame.quit()
