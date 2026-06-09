"""No-hardware tests for DM-S3519 USB-CAN feedback parsing."""

from base_omniwheel_r2_700.DM_CAN import DM_Motor_Type, Motor, MotorControl


class FakeSerial:
    """Minimal serial transport with buffered receive bytes."""

    def __init__(self, data=b""):
        self.is_open = True
        self._data = bytearray(data)

    @property
    def in_waiting(self):
        return len(self._data)

    def read(self, size):
        data = bytes(self._data[:size])
        del self._data[:size]
        return data

    def write(self, data):
        return len(data)


def make_feedback_frame(motor_id=3, status=1, mos_temp=40, rotor_temp=45):
    """Build one USB-CAN frame with centered q/dq/tau feedback."""
    payload = bytes([
        ((status & 0x0F) << 4) | (motor_id & 0x0F),
        0x80, 0x00, 0x80, 0x08, 0x00, mos_temp, rotor_temp,
    ])
    return (
        bytes([0xAA, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00])
        + payload
        + bytes([0x55])
    )


def test_feedback_uses_payload_id_and_status_nibbles():
    serial = FakeSerial(make_feedback_frame())
    controller = MotorControl(serial)
    motor = Motor(DM_Motor_Type.DMS3519, 3, 0)
    controller.addMotor(motor)

    controller.recv()

    assert motor.isEnable is True
    assert motor.error_code == 1
    assert motor.mos_temperature_c == 40
    assert motor.rotor_temperature_c == 45
    assert abs(motor.state_q) < 0.001
    assert abs(motor.state_dq) < 0.02
    assert abs(motor.state_tau) < 0.01


test_data = make_feedback_frame(motor_id=2, status=8)


def test_receive_parser_keeps_partial_frame_until_complete():
    serial = FakeSerial(test_data[:8])
    controller = MotorControl(serial)
    motor = Motor(DM_Motor_Type.DMS3519, 2, 0)
    controller.addMotor(motor)

    controller.recv()
    assert motor.last_feedback_time is None

    serial._data.extend(test_data[8:])
    controller.recv()

    assert motor.error_code == 8
    assert motor.isEnable is False
