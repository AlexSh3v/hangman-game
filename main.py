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
    for j, array in enumerate(letters_keyboard[LANGUAGE]):
        for i, letter in enumerate(array):

            if letter in hangman.guessed and letter in hangman.word:
                color = GREEN
                main_font.set_bold(True)
            elif letter in hangman.guessed and letter not in hangman.word:
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

            mouse_x, mouse_y = MouseController.get_instance().get()
            if letter_x <= mouse_x <= letter_x+text.get_width() and letter_y <= mouse_y <= letter_y+text.get_height():
                MouseController.get_instance().clicked_letter = letter


texture_dir = pathlib.Path(__file__).parent / 'textures'
AnchorValue = Literal['CENTER', 'NW', 'N', 'NE', 'S', 'W']


class HangmanGame:
    __instance = None
    __instance_count = 0

    def __init__(self):
        if self.__class__.__instance is not None:
            raise ValueError('this is Singleton Class!')

        self.is_lost = False
        self.is_won = False
        self.running = True
        self.word = ''
        self.blanks = ['_'] * len(self.word)
        self.guessed = set()
        self.scoring_system = ScoringSystem()

        self.__class__.__instance_count += 1
        if self.__class__.__instance_count > 1:
            raise ValueError('this is Singleton Class!')

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @property
    def is_game_over(self) -> bool:
        return self.is_lost or self.is_won
    
    def trigger_player_won(self):
        if self.is_won:
            return
        win_sound.play()
        self.scoring_system.streak += 1
        self.scoring_system.perk_freeze += 1
        if self.scoring_system.streak % 3 == 0:
            self.scoring_system.perk_hint += 1
        if is_chance(10):
            self.scoring_system.perk_nuka_bomb += 1
        self.is_won = True
        
    def trigger_lost(self):
        if self.is_lost:
            return
        head_cripple_sound.play()
        self.scoring_system.streak = 0
        self.is_lost = True
    
    def init_game(self):
        if self.is_lost:
            self.scoring_system.update_lost()
        elif self.is_won:
            self.scoring_system.update_won()
        self.is_lost = False
        self.is_won = False
        self.running = True
        MouseController.get_instance().pull_offscreen()
        self.setup_guessing_word()

    def try_to_guess(self, letter: str):
        if letter in self.word:
            self.fill_blank(letter)
            right_letter_sound.play()
        else:
            self.guessed.add(letter)
            wrong_letter_sound.play()
            if self.scoring_system.perk_nuka_bomb_active:
                self.scoring_system.skip_count += 1
            elif hangman.scoring_system.perk_freeze_active:
                hangman.scoring_system.skip_count += 1
                hangman.scoring_system.perk_freeze_active = False

    def fill_blank(self, letter: str):
        for i in range(len(self.word)):
            if self.word[i] == letter:
                self.blanks[i] = letter
                self.guessed.add(letter)

    @property
    def wrong_number_guessed(self):
        return len(set(self.word) - set(self.guessed))
   
    def is_guessed(self):
        return self.wrong_number_guessed == 0

    def setup_guessing_word(self):
        target_index = secrets.randbelow(words_total[LANGUAGE] + 1)
        with words_path[LANGUAGE].open() as txt:
            for i, line in enumerate(txt.readlines()):
                if i != target_index:
                    continue
                self.word = line.strip()
                break
        self.guessed.clear()
        self.blanks.clear()
        self.blanks.extend(['_'] * len(self.word))


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
        mouse_x, mouse_y = MouseController.get_instance().get()
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
            MouseController.get_instance().pull_offscreen()

    def update_won(self):
        self.longest_streak = max(self.streak, self.longest_streak)
        self.perk_freeze_active = False
        self.perk_hint_active = False
        self.perk_nuka_bomb_active = False
        self.skip_count = 0
        self.perk_nukes_array.clear()

    def update_lost(self):
        self.streak = 0
        self.perk_freeze_active = False
        self.perk_hint_active = False
        self.perk_nuka_bomb_active = False
        self.skip_count = 0
        self.perk_nukes_array.clear()
        

class MouseController:
    __instance = None
    __instance_count = 0

    def __init__(self):
        if self.__class__.__instance is not None:
            raise ValueError('this is Singleton Class!')
        self.mouse_x: int | float = -1
        self.mouse_y: int | float = -1
        self.clicked_letter: str = ''
        self.__class__.__instance_count += 1
        if self.__class__.__instance_count > 1:
            raise ValueError('this is Singleton Class!')

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def set_at(self, x: int | float, y: int | float):
        self.mouse_x = x
        self.mouse_y = y
        
    def get(self) -> tuple[int | float, int | float]:
        return self.mouse_x, self.mouse_y
    
    def pull_offscreen(self):
        self.mouse_x = -999
        self.mouse_y = -999


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


hangman = HangmanGame.get_instance()
hangman.init_game()
mouse_controller = MouseController.get_instance()

while hangman.running:

    hangman.scoring_system.update()

    if hangman.scoring_system.perk_hint_active:
        letter = None
        for let, _ in collections.Counter(hangman.word).most_common():
            if let not in hangman.blanks:
                letter = let
                break
        hangman.fill_blank(letter)
        right_letter_sound.play()
        hangman.scoring_system.perk_hint_active = False

    if hangman.is_guessed():
        hangman.trigger_player_won()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            hangman.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and hangman.is_game_over:
            hangman.init_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and not hangman.is_game_over:
            print(mouse_controller.get())
            mouse_controller.set_at(*event.pos)
            print(event.pos)

    clicked_letter = mouse_controller.clicked_letter
    if clicked_letter.isalpha() and not hangman.is_game_over:
        print(clicked_letter)

        if hangman.scoring_system.perk_nuka_bomb_active:
            result = get_letter_coordinates(letters_keyboard[LANGUAGE], clicked_letter)
            if result is None:
                raise ValueError(f'HOW LETTER {clicked_letter!r} GOT INTO {letters_keyboard[LANGUAGE]} ???')
            i, j = result
            explosion_sound.play()
            for letter in get_letters_in_radius(letters_keyboard[LANGUAGE], i, j, 1):
                hangman.try_to_guess(letter)
            hangman.scoring_system.perk_nuka_bomb_active = False
            hangman.scoring_system.perk_nukes_array.append(
                Object(
                    Objects.explosion_surface,
                    mouse_controller.get(), 'CENTER',
                )
            )
        else:
            hangman.try_to_guess(clicked_letter)

        mouse_controller.clicked_letter = ''
        mouse_controller.pull_offscreen()

    # Draw everything
    screen.fill(WHITE)

    hangman.scoring_system.draw()

    # FIGURE
    wrong_number_guessed = len(hangman.guessed - set(hangman.word))
    for i in range(len(Objects.hangman_figure)):
        if wrong_number_guessed-hangman.scoring_system.skip_count >= len(Objects.hangman_figure):
            hangman.trigger_lost()
        obj = Objects.hangman_figure[i]
        if i >= wrong_number_guessed-hangman.scoring_system.skip_count:
            obj.texture.set_alpha(40)
        else:
            obj.texture.set_alpha(255)
        obj.draw(*Objects.hangman_figure_delta)

    if hangman.is_won:
        main_font.set_bold(True)
        text = main_font.render(' '.join(hangman.word), True, GREEN)
    elif hangman.is_lost:
        main_font.set_bold(True)
        text = main_font.render(' '.join(hangman.word), True, RED)
    else:
        main_font.set_bold(False)
        text = main_font.render(' '.join(hangman.blanks), True, BLACK)
    screen.blit(text, (WIDTH/2 - text.get_width()/2, HEIGHT*8/10))

    draw_letter_keyboard()

    if hangman.scoring_system.perk_freeze_active:
        Objects.freeze_spiral.draw()

    if hangman.scoring_system.perk_nuka_bomb_active:
        Objects.nuke_warning.draw()
    for nuke in hangman.scoring_system.perk_nukes_array:
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
