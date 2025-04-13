import _thread
import sys
import time

from pynput import keyboard

from buzz_controller import BuzzController

buzz = BuzzController()
available_controllers = [0, 1, 2, 3]
running = True


def print_instructions():
    print("Buzz Controller Demo")
    print("Press the red button on the controller.")
    print("Press 'q' to exit the program.")


def handle_player_turn(controller):
    buzz.light_set(controller, True)
    time.sleep(5)

    button = buzz.get_button_pressed(controller)
    print(f"Controller: {controller}")

    if button and button != "red":
        if button == "blue":
            print("Controller " + str(controller) + " was correct")
            return True
        else:
            print("Sorry incorrect answer")
            available_controllers.remove(controller)
            return True

    buzz.light_set(controller, False)
    return False


def cleanup():
    global buzz, running
    running = False
    buzz.light_blinking = False
    time.sleep(0.1)
    for controller in range(4):
        buzz.light_set(controller, False)


def on_press(key):
    if key == keyboard.KeyCode.from_char("q"):
        print("Saliendo del programa...")
        cleanup()
        return False


def main():
    global running
    print_instructions()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        while running:
            blink_thread = _thread.start_new_thread(
                buzz.light_blink, (available_controllers,)
            )

            controller = buzz.controller_get_first_pressed("red", available_controllers)
            buzz.light_blinking = False

            if controller is None:
                if not running:
                    break
                continue

            if handle_player_turn(controller):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
        listener.stop()
        sys.exit(0)


if __name__ == "__main__":
    buzz.get_info()
    main()
