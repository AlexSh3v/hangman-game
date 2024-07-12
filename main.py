import dataclasses
import pathlib
import secrets
from typing import Literal

import pygame

# Initialize Pygame
pygame.init()

# Set up the font
project_dir = pathlib.Path(__file__).parent

words_path = {
    'en': project_dir / 'data' / 'en.txt',
    'ru': project_dir / 'data' / 'ru.txt',
}
words_total = {
    'en': 370_104,
    'ru': 137_000,
}
letters_keyboard = {
    'en': [
        ['a', 'b', 'c', 'd', 'e', 'f'],
        ['g', 'h', 'i', 'j', 'k', 'l'],
        ['m', 'n', 'o', 'p', 'q', 'r'],
        ['s', 't', 'u', 'v', 'w', 'x'],
        ['y', 'z']
    ],
    'ru': [
        ['а', 'б', 'в', 'г', 'д', 'е'],
        ['ё', 'ж', 'з', 'и', 'й', 'к'],
        ['л', 'м', 'н', 'о', 'п', 'р'],
        ['с', 'т', 'у', 'ф', 'х', 'ц'],
        ['ч', 'ш', 'щ', 'ъ', 'ы', 'ь'],
        ['э', 'ю', 'я']
    ],
}
LANGUAGE = 'ru'

comic_sans_font = pygame.font.Font(project_dir / 'fonts' / 'comic-sans.ttf', 42)

WIDTH, HEIGHT = 960, 540
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)

LETTERS_X = WIDTH - 400
LETTERS_Y = HEIGHT/5 - 50
LETTERS_GAP = 50
LETTERS_CELL_WIDTH = 40
LETTER_F_X = 0
LETTER_F_WIDTH = 0
LETTER_CLICKED = ''


def draw_letter_keyboard():
    global LETTER_CLICKED
    for j, array in enumerate(letters_keyboard[LANGUAGE]):
        for i, letter in enumerate(array):

            if letter in guessed and letter in word:
                color = GREEN
                comic_sans_font.set_bold(True)
            elif letter in guessed and letter not in word:
                color = RED
                comic_sans_font.set_bold(True)
            else:
                color = (0, 0, 0)
                comic_sans_font.set_bold(False)
            text = comic_sans_font.render(letter.upper(), True, color)
            w, h = text.get_size()
            extra_w = max(LETTERS_CELL_WIDTH - w, 0)
            letter_x = LETTERS_X + extra_w + LETTERS_GAP * i
            letter_y = LETTERS_Y + j * LETTERS_GAP
            screen.blit(text, (letter_x, letter_y))

            if letter_x <= mouse_x <= letter_x+text.get_width() and letter_y <= mouse_y <= letter_y+text.get_height():
                LETTER_CLICKED = letter


texture_dir = pathlib.Path(__file__).parent / 'textures'
AnchorValue = Literal['NW', 'N', 'NE', 'S', 'W']


@dataclasses.dataclass
class Object:
    texture: pygame.Surface
    pos: tuple[int, int]
    anchor: AnchorValue

    def draw(self, dx=0, dy=0):
        x, y = self.pos
        w, h = self.texture.get_size()
        if self.anchor == 'N':
            dest = (x-w/2, y)
        elif self.anchor == 'NW':
            dest = self.pos
        elif self.anchor == 'S':
            dest = (x-w/2, y-h)
        elif self.anchor == 'W':
            dest = (x, y-h/2)
        elif self.anchor == 'NE':
            dest = (x-w, y)
        else:
            raise ValueError(f'unknown anchor value {self.anchor!r}')
        dest = (dest[0] + dx, dest[1] + dy)
        screen.blit(self.texture, dest)


class Texture:
    wood_1 = pygame.image.load(texture_dir / 'wood-1.png')
    wood_2 = pygame.image.load(texture_dir / 'wood-2.png')
    wood_3 = pygame.image.load(texture_dir / 'wood-3.png')
    wood_4 = pygame.image.load(texture_dir / 'wood-4.png')
    wood_5 = pygame.image.load(texture_dir / 'wood-5.png')
    hangman_1 = pygame.image.load(texture_dir / 'hangman-1.png')
    hangman_2 = pygame.image.load(texture_dir / 'hangman-2.png')
    hangman_3 = pygame.image.load(texture_dir / 'hangman-3.png')
    hangman_4 = pygame.image.load(texture_dir / 'hangman-4.png')
    hangman_5 = pygame.image.load(texture_dir / 'hangman-5.png')
    hangman_6 = pygame.image.load(texture_dir / 'hangman-6.png')

    hangman_figure_delta = (-192 + 200, -135 + LETTERS_Y + 15)
    hangman_figure = [
        Object(wood_1, (200, 400), 'N'),
        Object(wood_2, (200, 420), 'S'),
        Object(wood_3, (182, 140), 'W'),
        Object(wood_4, (192, 135), 'NW'),
        Object(wood_5, (414, 132), 'N'),
        Object(hangman_1, (414, 194), 'N'),
        Object(hangman_2, (414, 257), 'N'),
        Object(hangman_3, (406, 262), 'NW'),
        Object(hangman_4, (420, 262), 'NE'),
        Object(hangman_5, (404, 352), 'NW'),
        Object(hangman_6, (425, 352), 'NE'),
    ]


# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hangman")


def setup_guessing_word():
    global word
    target_index = secrets.randbelow(words_total[LANGUAGE] + 1)
    with words_path[LANGUAGE].open() as txt:
        for i, line in enumerate(txt.readlines()):
            if i != target_index:
                continue
            word = line.strip()
            break
    guessed.clear()
    blanks.clear()
    blanks.extend(['_'] * len(word))


word = ''
blanks = []
guessed = set()
setup_guessing_word()

# Game loop
is_game_over = False
is_won = False
running = True
mouse_x = 0
mouse_y = 0
while running:
    print(f'MOUSE: ({mouse_x}, {mouse_y})')
    if len(set(word) - set(guessed)) == 0:
        is_won = True

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and (97 <= event.key <= 122):
            if is_game_over or is_won:
                continue
            letter = chr(event.key)

            # Check if the letter is in the word
            if letter in word:
                # Fill in the correct blanks
                for i in range(len(word)):
                    if word[i] == letter:
                        blanks[i] = letter
                        guessed.add(letter)
            else:
                guessed.add(letter)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if is_game_over or is_won:
                setup_guessing_word()
                is_game_over = False
                is_won = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not is_game_over and not is_won:
            mouse_x, mouse_y = event.pos

    if LETTER_CLICKED.isalpha() and not is_game_over and not is_won:
        # Check if the letter is in the word
        if LETTER_CLICKED in word:
            # Fill in the correct blanks
            for i in range(len(word)):
                if word[i] == LETTER_CLICKED:
                    blanks[i] = LETTER_CLICKED
                    guessed.add(LETTER_CLICKED)
        else:
            guessed.add(LETTER_CLICKED)
        LETTER_CLICKED = ''
        mouse_x, mouse_y = 0, 0

    # Draw everything
    screen.fill(WHITE)

    # FIGURE
    wrong_length = len(guessed - set(word))
    for i in range(len(Texture.hangman_figure)):
        if wrong_length >= len(Texture.hangman_figure):
            is_game_over = True
        obj = Texture.hangman_figure[i]
        if i >= wrong_length:
            obj.texture.set_alpha(40)
        else:
            obj.texture.set_alpha(255)
        obj.draw(*Texture.hangman_figure_delta)

    if is_won:
        comic_sans_font.set_bold(True)
        text = comic_sans_font.render(' '.join(word), True, GREEN)
    elif is_game_over:
        comic_sans_font.set_bold(True)
        text = comic_sans_font.render(' '.join(word), True, RED)
    else:
        comic_sans_font.set_bold(False)
        text = comic_sans_font.render(' '.join(blanks), True, BLACK)
    screen.blit(text, (WIDTH/2 - text.get_width()/2, HEIGHT*8/10))

    draw_letter_keyboard()

    # ::DEBUG-DRAWER::
    # POS = (425, 352)
    # print(262 + Texture.hangman_2.get_size()[1])
    # Texture.draw(Texture.hangman_6, POS, 'NE')
    # pygame.draw.circle(screen, (255, 0, 0), POS, 5)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
