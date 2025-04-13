import argparse

import i18n
import pygame
from pygame import mixer

from game import Game, create_main_menu
from i18n_config import change_language, setup_i18n

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


def main():
    parser = argparse.ArgumentParser(description="Guess the Song Community Ed")
    parser.add_argument(
        "--pack",
        type=str,
        default="pack_01",
        help="Song package directory to use (default: pack_01)",
    )
    args = parser.parse_args()

    setup_i18n()

    GAME_TITLE = i18n.t("game_title")

    pygame.init()
    mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    mixer.music.set_volume(1.0)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption(GAME_TITLE)

    game = Game(SCREEN_WIDTH, SCREEN_HEIGHT, song_pack=args.pack)
    menu = create_main_menu(game, SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE)

    running = True
    clock = pygame.time.Clock()

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif game.is_playing:
                        game.handle_event(event)

            screen.fill((0, 0, 0))

            if not game.is_playing:
                menu.mainloop(screen)
            else:
                game.update()
                game.draw(screen)

            pygame.display.flip()
            clock.tick(60)
    finally:
        if game.video_clip is not None:
            game.video_clip.close()
        game.cleanup()
        pygame.quit()


if __name__ == "__main__":
    main()
