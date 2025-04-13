import json
from pathlib import Path

import i18n
import pygame
import pygame_menu
from moviepy import VideoFileClip
from pygame import mixer

from buzz_controller import BuzzController


class Game:
    def __init__(self, screen_width, screen_height, song_pack="pack_01"):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.players = [
            {"name": "", "score": 0},
            {"name": "", "score": 0},
            {"name": "", "score": 0},
            {"name": "", "score": 0},
        ]
        self.version = "1.0.0"
        self.song_pack = song_pack
        self.current_category = 0
        self.current_song = 0
        self.songs_data = self.load_songs()
        self.is_playing = False
        self.last_action = None
        self.current_song_playing = None
        self.is_paused = False
        self.debug_message = ""
        self.debug_message_time = 0
        self.waiting_for_player = None
        self.show_controls = False
        self.is_video_playing = False
        self.video_clip = None
        self.video_frame = None
        self.video_start_time = 0
        self.buzz_controller = BuzzController()
        self.available_controllers = [0, 1, 2, 3]
        self.is_buzz_round_active = False
        self.buzz_start_time = 0
        self.last_buzz_check = 0
        self.buzz_check_interval = 0.1
        self.blink_state = False
        self.last_blink_time = 0
        self.blink_interval = 0.5
        self.show_scores = False

        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 72)

    def update_translations(self):
        pass

    def load_songs(self):
        try:
            songs_file = Path(f"data/{self.song_pack}/songs.json")
            with open(songs_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo data/{self.song_pack}/songs.json")
            return {"categories": []}
        except json.JSONDecodeError:
            print(
                f"Error: El archivo data/{self.song_pack}/songs.json no tiene un formato JSON válido"
            )
            return {"categories": []}

    def start_game(self):
        self.is_playing = True
        self.current_category = 0
        self.current_song = 0
        self.play_current_song()
        self.start_buzz_round()
        return True

    def next_category(self):
        if self.current_category < len(self.songs_data["categories"]) - 1:
            self.current_category += 1
            self.current_song = 0
            self.play_current_song()
            self.set_debug_message(
                f"{i18n.t('next_category')} {self.songs_data['categories'][self.current_category]['name']}"
            )

    def previous_category(self):
        if self.current_category > 0:
            self.current_category -= 1
            self.current_song = 0
            self.play_current_song()
            self.set_debug_message(
                f"{i18n.t('prev_category')} {self.songs_data['categories'][self.current_category]['name']}"
            )

    def next_song(self):
        current_category = self.songs_data["categories"][self.current_category]
        if self.current_song < len(current_category["songs"]) - 1:
            self.current_song += 1
            self.play_current_song()
            self.set_debug_message(i18n.t("next_song"))
            self.start_buzz_round()

    def previous_song(self):
        if self.current_song > 0:
            self.current_song -= 1
            self.play_current_song()
            self.set_debug_message(i18n.t("prev_song"))

    def play_current_song(self):
        if self.current_song_playing:
            mixer.music.stop()
        current_song = self.songs_data["categories"][self.current_category]["songs"][
            self.current_song
        ]
        try:
            file_path = Path(f"data/{self.song_pack}") / current_song["file"]
            if not file_path.exists():
                self.set_debug_message(f"Error: No se encontró el archivo {file_path}")
                return

            if file_path.suffix.lower() == ".m4a":
                try:
                    mixer.music.load(str(file_path))
                    mixer.music.play()
                    self.current_song_playing = current_song
                    self.is_paused = False
                    self.set_debug_message(
                        f"{i18n.t('playing')} {current_song['title']}"
                    )
                except Exception as e:
                    self.set_debug_message(f"Error al reproducir M4A: {str(e)}")
                    print(f"Error detallado al reproducir M4A: {str(e)}")
            else:
                mixer.music.load(str(file_path))
                mixer.music.play()
                self.current_song_playing = current_song
                self.is_paused = False
                self.set_debug_message(f"{i18n.t('playing')} {current_song['title']}")
        except Exception as e:
            self.set_debug_message(f"Error al cargar la canción: {str(e)}")
            print(f"Error al cargar la canción: {file_path}")
            print(f"Error detallado: {str(e)}")

    def toggle_pause(self):
        if self.current_song_playing:
            if not self.is_paused:
                mixer.music.pause()
                self.is_paused = True
                for controller in self.available_controllers:
                    self.buzz_controller.light_set(controller, False)
                self.is_buzz_round_active = False
                self.set_debug_message(i18n.t("song_paused"))
            else:
                mixer.music.unpause()
                self.is_paused = False
                self.start_buzz_round()
                self.set_debug_message(i18n.t("song_resumed"))

    def pause_for_player(self, player_index):
        if mixer.music.get_busy() and not self.is_paused:
            mixer.music.pause()
            self.is_paused = True
            self.waiting_for_player = player_index
            player_name = (
                self.players[player_index]["name"]
                if self.players[player_index]["name"]
                else f"{i18n.t('player')} {player_index + 1}"
            )
            self.set_debug_message(f"{i18n.t('waiting_for_answer')} {player_name}")

    def resume_song(self):
        if self.is_paused:
            mixer.music.unpause()
            self.is_paused = False
            self.waiting_for_player = None
            self.set_debug_message(i18n.t("song_resumed"))

    def add_points(self, player_index, points):
        if self.waiting_for_player == player_index:
            new_score = self.players[player_index]["score"] + points
            if new_score < 0:
                points = -self.players[player_index]["score"]
                new_score = 0

            self.last_action = {"player": player_index, "points": points}
            self.players[player_index]["score"] = new_score
            player_name = (
                self.players[player_index]["name"]
                or f"{i18n.t('player')} {player_index + 1}"
            )
            points_text = (
                i18n.t("correct_answer") if points > 0 else i18n.t("wrong_answer")
            )
            self.set_debug_message(
                f"{player_name} {points_text} {abs(points)} {i18n.t('points')}"
            )
            self.waiting_for_player = None

    def undo_last_action(self):
        if self.last_action:
            self.players[self.last_action["player"]]["score"] -= self.last_action[
                "points"
            ]
            player_name = (
                self.players[self.last_action["player"]]["name"]
                or f"{i18n.t('player')} {self.last_action['player'] + 1}"
            )
            self.set_debug_message(f"{i18n.t('undo_action')} {player_name}")
            self.last_action = None

    def toggle_video(self):
        if self.is_video_playing:
            self.stop_video()
        else:
            self.play_video()

    def play_video(self):
        current_song = self.songs_data["categories"][self.current_category]["songs"][
            self.current_song
        ]
        video_path = current_song.get("video", False)

        if not video_path or video_path == "false":
            self.set_debug_message(i18n.t("no_video"))
            return

        video_path = Path(f"data/{self.song_pack}") / video_path
        if not video_path.exists():
            self.set_debug_message(i18n.t("video_not_found"))
            return

        try:
            self.video_clip = VideoFileClip(str(video_path))
            self.is_video_playing = True
            self.video_start_time = pygame.time.get_ticks() / 1000.0
            self.set_debug_message(i18n.t("playing_video"))
        except Exception as e:
            self.set_debug_message(f"Error al cargar el video: {str(e)}")

    def stop_video(self):
        if self.video_clip is not None:
            self.video_clip.close()
            self.video_clip = None
        self.is_video_playing = False
        self.video_frame = None
        self.set_debug_message(i18n.t("video_stopped"))

    def update_video_frame(self):
        if self.is_video_playing and self.video_clip is not None:
            try:
                current_time = pygame.time.get_ticks() / 1000.0 - self.video_start_time

                if current_time < self.video_clip.duration:
                    frame = self.video_clip.get_frame(current_time)
                    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                    self.video_frame = frame
                else:
                    self.stop_video()
            except Exception as e:
                self.set_debug_message(f"Error al actualizar frame: {str(e)}")
                self.stop_video()

    def set_debug_message(self, message):
        self.debug_message = message
        self.debug_message_time = pygame.time.get_ticks()

    def update_debug_message(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.debug_message_time > 5000:
            self.debug_message = ""

    def draw(self, screen):
        screen.fill((0, 0, 0))

        if self.is_video_playing:
            self.update_video_frame()

        player_y = 50
        for i, player in enumerate(self.players, 1):
            if self.show_scores:
                player_text = f"{i18n.t('player')} {i}: {player['name']} - {player['score']} {i18n.t('points')}"
            else:
                player_text = f"{i18n.t('player')} {i}: {player['name']}"
            text_surface = self.font.render(player_text, True, (255, 255, 255))
            screen.blit(text_surface, (20, player_y))
            player_y += 40

        if self.songs_data["categories"]:
            current_category = self.songs_data["categories"][self.current_category]
            current_song = current_category["songs"][self.current_song]

            category_text = f"{i18n.t('category')}: {current_category['name']}"
            song_text = f"{i18n.t('track')}: {self.current_song + 1}/{len(current_category['songs'])}"

            category_surface = self.font.render(category_text, True, (255, 255, 255))
            song_surface = self.font.render(song_text, True, (255, 255, 255))

            screen.blit(category_surface, (20, player_y + 20))
            screen.blit(song_surface, (20, player_y + 60))

        if (
            self.debug_message
            and pygame.time.get_ticks() - self.debug_message_time < 3000
        ):
            debug_surface = self.font.render(self.debug_message, True, (255, 255, 255))
            screen.blit(debug_surface, (20, self.screen_height - 40))

        if self.show_controls:
            help_surface = pygame.Surface((self.screen_width // 2, self.screen_height))
            help_surface.set_alpha(128)
            help_surface.fill((0, 0, 0))
            screen.blit(help_surface, (self.screen_width // 2, 0))

            controls = [
                i18n.t("controls.title"),
                i18n.t("controls.pause"),
                i18n.t("controls.navigate"),
                i18n.t("controls.correct"),
                i18n.t("controls.wrong"),
                i18n.t("controls.video"),
                i18n.t("controls.buzz"),
                i18n.t("controls.help"),
                i18n.t("controls.scores"),
            ]

            help_y = 50
            for control in controls:
                control_surface = self.font.render(control, True, (255, 255, 255))
                screen.blit(control_surface, (self.screen_width // 2 + 20, help_y))
                help_y += 40

        if self.is_video_playing and self.video_frame is not None:
            try:
                video_width = self.video_frame.get_width()
                video_height = self.video_frame.get_height()
                screen_width = self.screen_width
                screen_height = self.screen_height

                scale = min(screen_width / video_width, screen_height / video_height)
                new_width = int(video_width * scale)
                new_height = int(video_height * scale)

                scaled_frame = pygame.transform.scale(
                    self.video_frame, (new_width, new_height)
                )
                x = (screen_width - new_width) // 2
                y = (screen_height - new_height) // 2
                screen.blit(scaled_frame, (x, y))
            except Exception as e:
                self.set_debug_message(f"Error al dibujar video: {str(e)}")
                self.stop_video()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                if self.waiting_for_player is not None:
                    self.add_points(self.waiting_for_player, 5)
                    self.resume_song()
            elif event.key == pygame.K_a and self.waiting_for_player is not None:
                self.add_points(self.waiting_for_player, -3)
                self.resume_song()
            elif event.key == pygame.K_SPACE:
                self.toggle_pause()
            elif event.key == pygame.K_RIGHT:
                self.next_song()
            elif event.key == pygame.K_LEFT:
                self.previous_song()
            elif event.key == pygame.K_UP:
                self.next_category()
            elif event.key == pygame.K_DOWN:
                self.previous_category()
            elif event.key == pygame.K_1:
                self.pause_for_player(0)
            elif event.key == pygame.K_2:
                self.pause_for_player(1)
            elif event.key == pygame.K_3:
                self.pause_for_player(2)
            elif event.key == pygame.K_4:
                self.pause_for_player(3)
            elif event.key == pygame.K_ESCAPE:
                self.is_playing = False
            elif event.key == pygame.K_h:
                self.show_controls = not self.show_controls
            elif event.key == pygame.K_v:
                self.toggle_video()
            elif event.key == pygame.K_s:
                self.show_scores = not self.show_scores
                scores_status = (
                    i18n.t("scores_shown")
                    if self.show_scores
                    else i18n.t("scores_hidden")
                )
                self.set_debug_message(scores_status)

    def start_buzz_round(self):
        if not self.is_buzz_round_active:
            self.is_buzz_round_active = True
            self.buzz_start_time = pygame.time.get_ticks() / 1000.0
            self.last_buzz_check = self.buzz_start_time
            self.last_blink_time = self.buzz_start_time
            self.blink_state = True
            self.set_debug_message(i18n.t("press_buzz"))
            for controller in self.available_controllers:
                self.buzz_controller.light_set(controller, True)

    def update(self):
        current_time = pygame.time.get_ticks() / 1000.0

        if self.is_buzz_round_active:
            if current_time - self.last_blink_time >= self.blink_interval:
                self.last_blink_time = current_time
                self.blink_state = not self.blink_state
                for controller in self.available_controllers:
                    self.buzz_controller.light_set(controller, self.blink_state)

            if current_time - self.last_buzz_check >= self.buzz_check_interval:
                self.last_buzz_check = current_time

                button_states = self.buzz_controller.get_button_status()

                for controller in self.available_controllers:
                    if button_states[controller]["red"]:
                        self.is_buzz_round_active = False
                        for c in self.available_controllers:
                            self.buzz_controller.light_set(c, False)
                        self.buzz_controller.light_set(controller, True)
                        self.pause_for_player(controller)
                        player_text = f"{i18n.t('player')} {controller + 1}"
                        self.set_debug_message(
                            f"¡{player_text} {i18n.t('player_pressed')}!"
                        )
                        return

    def cleanup(self):
        if self.buzz_controller:
            for controller in range(4):
                self.buzz_controller.light_set(controller, False)


def create_main_menu(game, screen_width, screen_height, game_title):
    menu = pygame_menu.Menu(
        game_title,
        screen_width,
        screen_height,
        theme=pygame_menu.themes.THEME_DARK,
    )

    def update_player1_name(value):
        game.players[0]["name"] = value

    def update_player2_name(value):
        game.players[1]["name"] = value

    def update_player3_name(value):
        game.players[2]["name"] = value

    def update_player4_name(value):
        game.players[3]["name"] = value

    def start_game():
        game.start_game()
        menu.disable()

    menu.add.text_input(
        f"{i18n.t('player')} 1: ", default="", onchange=update_player1_name
    )
    menu.add.text_input(
        f"{i18n.t('player')} 2: ", default="", onchange=update_player2_name
    )
    menu.add.text_input(
        f"{i18n.t('player')} 3: ", default="", onchange=update_player3_name
    )
    menu.add.text_input(
        f"{i18n.t('player')} 4: ", default="", onchange=update_player4_name
    )
    menu.add.button(i18n.t("play"), start_game)
    menu.add.button(i18n.t("exit"), pygame_menu.events.EXIT)

    version_label = menu.add.label(
        f"{i18n.t('version')} {game.version}", align=pygame_menu.locals.ALIGN_RIGHT
    )
    version_label.set_position(0, screen_height - 30)

    return menu
