import sys
import threading
import time
from unittest.mock import MagicMock

import pytest

# Mock hid before importing BuzzController
hid_mock = MagicMock()
class FakeHIDException(Exception):
    pass
hid_mock.HIDException = FakeHIDException
sys.modules["hid"] = hid_mock

from buzz_controller import BuzzController


@pytest.fixture
def mock_hid_device():
    device = MagicMock()
    hid_mock.Device.return_value = device
    return device

def test_init_calls_hid_device_and_write(mock_hid_device):
    controller = BuzzController()
    hid_mock.Device.assert_called_with(0x54C, 0x02)
    assert mock_hid_device.write.call_count == 1
    assert mock_hid_device.nonblocking == 1

def test_init_exits_on_exception(monkeypatch):
    hid_mock.Device.side_effect = IOError("fail")
    with pytest.raises(SystemExit):
        BuzzController()
    hid_mock.Device.side_effect = None

def test_light_blink_and_stop(monkeypatch, mock_hid_device):
    controller = BuzzController()
    controller.light_blinking = False

    # Patch time.sleep to fast-forward blinking
    monkeypatch.setattr("time.sleep", lambda x: None)
    # Patch hid.write to count calls
    calls = []
    def fake_write(data):
        calls.append(bytes(data))
    mock_hid_device.write.side_effect = fake_write

    # Run light_blink in a way that it stops after one blink
    def stop_blink(*args, **kwargs):
        controller.light_blinking = False
    monkeypatch.setattr(controller, "light_blinking", False)
    t = threading.Thread(target=controller.light_blink, args=([1,2],))
    t.start()
    time.sleep(0.01)
    controller.light_blinking = False
    t.join(timeout=0.1)
    assert any(calls)

def test_get_button_status_sets_button_states(mock_hid_device):
    controller = BuzzController()
    # Simulate data for player 0 red and player 1 blue pressed
    mock_hid_device.read.return_value = [0, 0, 0x21, 0x02, 0x00]
    states = controller.get_button_status()
    assert states[0]["red"] is True
    assert states[1]["blue"] is True

def test_get_button_pressed_returns_correct_button(mock_hid_device):
    controller = BuzzController()
    # Simulate only player 2 green pressed
    mock_hid_device.read.return_value = [0, 0, 0x00, 0x10, 0x00]
    btn = controller.get_button_pressed(2)
    assert btn == "green"

def test_controller_get_first_pressed_returns_controller(monkeypatch, mock_hid_device):
    controller = BuzzController()
    # Simulate player 1 red pressed
    states = [
        [0, 0, 0x20, 0x00, 0x00],  # Only player 1 red
        [0, 0, 0x00, 0x00, 0x00],  # No buttons
    ]
    mock_hid_device.read.side_effect = lambda n: states.pop(0) if states else [0,0,0,0,0]
    monkeypatch.setattr("time.sleep", lambda x: None)
    idx = controller.controller_get_first_pressed("red", [0,1,2,3], timeout=0.1)
    assert idx == 1

def test_controller_get_first_pressed_timeout(monkeypatch, mock_hid_device):
    controller = BuzzController()
    mock_hid_device.read.return_value = [0,0,0,0,0]
    monkeypatch.setattr("time.sleep", lambda x: None)
    idx = controller.controller_get_first_pressed("red", [0,1,2,3], timeout=0.01)
    assert idx is None

def test_light_blink_stop_sets_flag(mock_hid_device):
    controller = BuzzController()
    controller.light_blinking = True
    controller.light_blink_stop()
    assert controller.light_blinking is False

def test_light_set_writes_correct_array(mock_hid_device):
    controller = BuzzController()
    controller.light_array = bytes([0]*8)
    controller.light_set(1, True)
    # Controller 1 sets index 3 to 0xFF
    expected = bytearray([0,0,0,0xFF,0,0,0,0])
    mock_hid_device.write.assert_called_with(bytes(expected))

def test_get_info_prints(monkeypatch, mock_hid_device, capsys):
    controller = BuzzController()
    mock_hid_device.__enter__.return_value.manufacturer = "Sony"
    mock_hid_device.__enter__.return_value.product = "Buzz"
    controller.get_info()
    out = capsys.readouterr().out
    assert "Sony" in out
    assert "Buzz" in out
