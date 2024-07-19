import collections
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
    'ru': project_dir / 'data' / 'ru_nouns.txt',  # https://github.com/codemurt/russian-words?tab=readme-ov-file
}
words_total = {
    'en': 370_104,
    'ru': 21_320,
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

# Load the sound effect
win_sound = pygame.mixer.Sound(project_dir / 'audio' / 'xp_up.mp3')
hint_sound = pygame.mixer.Sound(project_dir / 'audio' / 'hint.wav')
explosion_sound = pygame.mixer.Sound(project_dir / 'audio' / 'explosion.mp3')
head_cripple_sound = pygame.mixer.Sound(project_dir / 'audio' / 'head_cripple.mp3')
right_letter_sound = pygame.mixer.Sound(project_dir / 'audio' / 'right_letter.mp3')
wrong_letter_sound = pygame.mixer.Sound(project_dir / 'audio' / 'wrong_letter.mp3')

main_font = pygame.font.Font(project_dir / 'fonts' / 'comic-sans.ttf', 42)
ui_font = pygame.font.Font(project_dir / 'fonts' / 'comic-sans.ttf', 32)

WIDTH, HEIGHT = 960, 540
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
YELLLOW = (215, 240, 0)

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
                main_font.set_bold(True)
            elif letter in guessed and letter not in word:
                color = RED
                main_font.set_bold(True)
            else:
                color = (0, 0, 0)
                main_font.set_bold(False)
            text = main_font.render(letter.upper(), True, color)
            w, h = text.get_size()
            extra_w = max(LETTERS_CELL_WIDTH - w, 0)
            letter_x = LETTERS_X + extra_w + LETTERS_GAP * i
            letter_y = LETTERS_Y + j * LETTERS_GAP
            screen.blit(text, (letter_x, letter_y))

            if letter_x <= mouse_x <= letter_x+text.get_width() and letter_y <= mouse_y <= letter_y+text.get_height():
                LETTER_CLICKED = letter


texture_dir = pathlib.Path(__file__).parent / 'textures'
AnchorValue = Literal['CENTER', 'NW', 'N', 'NE', 'S', 'W']


@dataclasses.dataclass
class Object:
    texture: pygame.Surface
    pos: tuple[int, int]
    anchor: AnchorValue

    def __post_init__(self):
        self.__scaling_factors = (1, 1)

    def fill(self, color):
        w, h = self.texture.get_size()
        r, g, b, *a = color
        alpha = None
        if a:
            alpha = a[0]
        for x in range(w):
            for y in range(h):
                a = self.texture.get_at((x, y))[3]
                if a > 0 and alpha is not None:
                    a = alpha
                self.texture.set_at((x, y), pygame.Color(r, g, b, a))

    def scale(self, dw: float, dh: float):
        w, h = self.texture.get_size()
        return Object(
            pygame.transform.scale(self.texture, (w*dw, h*dh)),
            self.pos, self.anchor,
        )

    def is_clicked(self) -> bool:
        x, y = self.pos
        w, h = self.texture.get_size()
        return x <= mouse_x <= x+w and y <= mouse_y <= y+h

    def draw(self, dx=0, dy=0, color=None) -> tuple[int, int, int, int]:
        if color is None:
            color = BLACK
        x, y = self.pos
        w, h = self.texture.get_size()
        # self.fill(color)
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
        elif self.anchor == 'CENTER':
            dest = (x-w/2, y-h/2)
        else:
            raise ValueError(f'unknown anchor value {self.anchor!r}')
        dest = (dest[0] + dx, dest[1] + dy)
        screen.blit(self.texture, dest)
        return x, y, w, h


class Objects:
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

    streak_icon = Object(
        pygame.image.load(texture_dir / 'streak.png'),
        (0, 0), 'NW'
    ).scale(0.2, 0.2)

    _start_y = LETTERS_Y+30
    perk_freeze = Object(
        pygame.image.load(texture_dir / 'freeze_spiral_black.png'),
        (10, _start_y), 'NW'
    ).scale(0.10, 0.10)
    perk_hint = Object(
        pygame.image.load(texture_dir / 'perk_hint.png'),
        (0, _start_y*1.70), 'NW'
    ).scale(0.3, 0.3)
    perk_nuka_bomb = Object(
        pygame.image.load(texture_dir / 'perk_nuka_bomb.png'),
        (10, _start_y*2.60), 'NW'
    ).scale(0.2, 0.2)

    freeze_spiral = Object(
        pygame.image.load(texture_dir / 'freeze_spiral_blue.png'),
        (WIDTH * 0.20, HEIGHT * 0.45), 'W'
    ).scale(0.5, 0.5)
    explosion_surface = pygame.image.load(texture_dir / 'explosion.png')
    nuke_warning = Object(
        pygame.image.load(texture_dir / 'nuke-warning.png'),
        (WIDTH * 0.20, HEIGHT * 0.45), 'W'
    ).scale(0.5, 0.5)

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


@dataclasses.dataclass
class ScoringSystem:
    streak: int = 0
    longest_streak: int = 0

    perk_freeze: int = 0
    perk_hint: int = 0
    perk_nuka_bomb: int = 0

    perk_freeze_active: bool = False
    perk_hint_active: bool = False
    perk_nuka_bomb_active: bool = False

    skip_count: int = 0
    perk_nukes_array: list[Object] = dataclasses.field(default_factory=list)

    @staticmethod
    def draw_icon(obj: Object, number: int, color=None):
        if color is None:
            color = BLACK if number > 0 else RED
        x, y, w, h = obj.draw(color=color)
        dw = w * 0.75
        dh = h * 0.50
        ui_font.set_italic(True)
        text = ui_font.render(str(number), True, color)
        screen.blit(text, (x+dw, y+dh))
        ui_font.set_italic(False)

    def draw(self):
        ScoringSystem.draw_icon(Objects.streak_icon, self.streak, YELLLOW)
        ScoringSystem.draw_icon(Objects.perk_freeze, self.perk_freeze)
        ScoringSystem.draw_icon(Objects.perk_hint, self.perk_hint)
        ScoringSystem.draw_icon(Objects.perk_nuka_bomb, self.perk_nuka_bomb)

    def update(self):
        global mouse_x

        is_clicked = False

        if Objects.streak_icon.is_clicked() and self.streak >= 10:
            self.streak -= 10
            self.perk_nuka_bomb += 1
            win_sound.play()
            is_clicked = True

        if Objects.perk_freeze.is_clicked() and self.perk_freeze > 0 and not self.perk_freeze_active:
            self.perk_freeze_active = True
            self.perk_freeze -= 1
            hint_sound.play()
            is_clicked = True

        if Objects.perk_hint.is_clicked() and self.perk_hint > 0 and not self.perk_hint_active:
            self.perk_hint_active = True
            self.perk_hint -= 1
            is_clicked = True

        if Objects.perk_nuka_bomb.is_clicked() and self.perk_nuka_bomb > 0 and not self.perk_nuka_bomb_active:
            self.perk_nuka_bomb_active = True
            self.perk_nuka_bomb -= 1
            is_clicked = True

        if is_clicked:
            mouse_x = -100

    def update_won(self):
        print('WON!!!')
        self.longest_streak = max(self.streak, self.longest_streak)
        self.perk_freeze_active = False
        self.perk_hint_active = False
        self.perk_nuka_bomb_active = False
        self.skip_count = 0
        self.perk_nukes_array.clear()

    def update_lost(self):
        print('LOST!!!')
        self.streak = 0
        self.perk_freeze_active = False
        self.perk_hint_active = False
        self.perk_nuka_bomb_active = False
        self.skip_count = 0
        self.perk_nukes_array.clear()


def get_letters_in_radius(arr, x, y, radius):
    for i in range(x - radius, x + radius + 1):
        for j in range(y - radius, y + radius + 1):
            if 0 <= i < len(arr) and 0 <= j < len(arr[i]):
                yield arr[i][j]


def get_letter_coordinates(arr, letter):
    for i, row in enumerate(arr):
        for j, elem in enumerate(row):
            if elem == letter:
                return i, j
    return None


def is_chance(percent: int) -> bool:
    return (secrets.randbelow(100) + 1) <= percent


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
scoring = ScoringSystem()
while running:

    scoring.update()

    if scoring.perk_hint_active:
        letter = None
        for let, _ in collections.Counter(word).most_common():
            if let not in blanks:
                letter = let
                break
        for i in range(len(word)):
            if word[i] == letter:
                blanks[i] = letter
                guessed.add(letter)
        right_letter_sound.play()
        scoring.perk_hint_active = False

    if len(set(word) - set(guessed)) == 0:
        if not is_won:
            win_sound.play()
            scoring.streak += 1
            scoring.perk_freeze += 1
            if scoring.streak % 3 == 0:
                scoring.perk_hint += 1
            if is_chance(10):
                scoring.perk_nuka_bomb += 1
        is_won = True

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if is_game_over or is_won:
                setup_guessing_word()
                if is_game_over:
                    scoring.update_lost()
                elif is_won:
                    scoring.update_won()
                is_game_over = False
                is_won = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not is_game_over and not is_won:
            mouse_x, mouse_y = event.pos

    if LETTER_CLICKED.isalpha() and not is_game_over and not is_won:

        if scoring.perk_nuka_bomb_active:
            result = get_letter_coordinates(letters_keyboard[LANGUAGE], LETTER_CLICKED)
            if result is None:
                raise ValueError(f'HOW LETTER {LETTER_CLICKED!r} GOT INTO {letters_keyboard[LANGUAGE]} ???')
            i, j = result
            explosion_sound.play()
            for letter in get_letters_in_radius(letters_keyboard[LANGUAGE], i, j, 1):
                if letter in word:
                    for i in range(len(word)):
                        if word[i] == letter:
                            blanks[i] = letter
                            guessed.add(letter)
                    right_letter_sound.play()
                else:
                    guessed.add(letter)
                    wrong_letter_sound.play()
                    scoring.skip_count += 1
            scoring.perk_nuka_bomb_active = False
            scoring.perk_nukes_array.append(
                Object(
                    Objects.explosion_surface,
                    (mouse_x, mouse_y), 'CENTER',
                )
            )
        else:
            # Check if the letter is in the word
            if LETTER_CLICKED in word:
                # Fill in the correct blanks
                for i in range(len(word)):
                    if word[i] == LETTER_CLICKED:
                        blanks[i] = LETTER_CLICKED
                        guessed.add(LETTER_CLICKED)
                right_letter_sound.play()
            else:
                guessed.add(LETTER_CLICKED)
                wrong_letter_sound.play()
                if scoring.perk_freeze_active:
                    scoring.skip_count += 1
                    scoring.perk_freeze_active = False

        LETTER_CLICKED = ''
        mouse_x, mouse_y = 0, 0

    # Draw everything
    screen.fill(WHITE)

    scoring.draw()

    # FIGURE
    wrong_length = len(guessed - set(word))
    print(word, wrong_length - scoring.skip_count, len(Objects.hangman_figure))
    for i in range(len(Objects.hangman_figure)):
        if wrong_length-scoring.skip_count >= len(Objects.hangman_figure):
            if not is_game_over:
                head_cripple_sound.play()
                scoring.streak = 0
            is_game_over = True
        obj = Objects.hangman_figure[i]
        if i >= wrong_length-scoring.skip_count:
            obj.texture.set_alpha(40)
        else:
            obj.texture.set_alpha(255)
        obj.draw(*Objects.hangman_figure_delta)

    if is_won:
        main_font.set_bold(True)
        text = main_font.render(' '.join(word), True, GREEN)
    elif is_game_over:
        main_font.set_bold(True)
        text = main_font.render(' '.join(word), True, RED)
    else:
        main_font.set_bold(False)
        text = main_font.render(' '.join(blanks), True, BLACK)
    screen.blit(text, (WIDTH/2 - text.get_width()/2, HEIGHT*8/10))

    draw_letter_keyboard()

    if scoring.perk_freeze_active:
        Objects.freeze_spiral.draw()

    if scoring.perk_nuka_bomb_active:
        Objects.nuke_warning.draw()
    for nuke in scoring.perk_nukes_array:
        nuke.draw()

    # ::DEBUG-DRAWER::
    # POS = (425, 352)
    # print(262 + Texture.hangman_2.get_size()[1])
    # Texture.draw(Texture.hangman_6, POS, 'NE')
    # pygame.draw.circle(screen, (255, 0, 0), POS, 5)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
