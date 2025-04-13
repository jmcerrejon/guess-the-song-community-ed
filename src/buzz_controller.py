import time

import hid


class BuzzController:
    light_array = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    light_blinking = False
    buttonState = [
        {"red": False, "blue": False, "orange": False, "green": False, "yellow": False},
        {"red": False, "blue": False, "orange": False, "green": False, "yellow": False},
        {"red": False, "blue": False, "orange": False, "green": False, "yellow": False},
        {"red": False, "blue": False, "orange": False, "green": False, "yellow": False},
    ]
    vid = 0x54C
    pid = 0x02

    def __init__(self):
        try:
            self.hid = hid.Device(self.vid, self.pid)
            self.hid.nonblocking = 1
            self.hid.write(self.light_array)
        except (IOError, ValueError, hid.HIDException) as e:
            print(
                "Error: Buzz Controller not detected. Please connect the controller before starting."
            )
            import sys

            sys.exit(1)

    def light_blink(self, controller):
        blink_lights_off = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.blink_lights_on = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        for i in controller:
            self.blink_lights_on = (
                self.blink_lights_on[: i + 2]
                + bytes([0xFF])
                + self.blink_lights_on[i + 3 :]
            )

        if not self.light_blinking:
            self.light_blinking = True
            blink = True
            while self.light_blinking:
                if blink:
                    self.hid.write(self.blink_lights_on)
                else:
                    self.hid.write(blink_lights_off)
                blink = not blink
                time.sleep(0.5)

            self.hid.write(self.light_array)

    def get_button_status(self):
        data = self.hid.read(5)
        if data:
            self.buttonState[0]["red"] = (data[2] & 0x01) != 0
            self.buttonState[0]["yellow"] = (data[2] & 0x02) != 0
            self.buttonState[0]["green"] = (data[2] & 0x04) != 0
            self.buttonState[0]["orange"] = (data[2] & 0x08) != 0
            self.buttonState[0]["blue"] = (data[2] & 0x10) != 0

            self.buttonState[1]["red"] = (data[2] & 0x20) != 0
            self.buttonState[1]["yellow"] = (data[2] & 0x40) != 0
            self.buttonState[1]["green"] = (data[2] & 0x80) != 0
            self.buttonState[1]["orange"] = (data[3] & 0x01) != 0
            self.buttonState[1]["blue"] = (data[3] & 0x02) != 0

            self.buttonState[2]["red"] = (data[3] & 0x04) != 0
            self.buttonState[2]["yellow"] = (data[3] & 0x08) != 0
            self.buttonState[2]["green"] = (data[3] & 0x10) != 0
            self.buttonState[2]["orange"] = (data[3] & 0x20) != 0
            self.buttonState[2]["blue"] = (data[3] & 0x40) != 0

            self.buttonState[3]["red"] = (data[3] & 0x80) != 0
            self.buttonState[3]["yellow"] = (data[4] & 0x01) != 0
            self.buttonState[3]["green"] = (data[4] & 0x02) != 0
            self.buttonState[3]["orange"] = (data[4] & 0x04) != 0
            self.buttonState[3]["blue"] = (data[4] & 0x08) != 0
        return self.buttonState

    def get_button_pressed(self, controller):
        buttons = self.get_button_status()
        for key, value in buttons[controller].items():
            if value:
                return key

    def controller_get_first_pressed(
        self, buzzButton, controllers=[0, 1, 2, 3], timeout=1.0
    ):
        start_time = time.time()
        while True:
            buttons = self.get_button_status()
            for i in controllers:
                if buttons[i][buzzButton]:
                    return i

            if time.time() - start_time > timeout:
                return None

            time.sleep(0.01)

    def light_blink_stop(self):
        self.light_blinking = False

    def light_set(self, controller, status):
        temp_array = bytearray(self.light_array)
        temp_array[controller + 2] = 0xFF if status else 0x00
        self.light_array = bytes(temp_array)
        self.hid.write(self.light_array)

    def get_info(self):
        with self.hid as h:
            print(f"Device manufacturer: {h.manufacturer}")
            print(f"Product: {h.product}")
