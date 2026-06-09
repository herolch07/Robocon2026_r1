from time import monotonic, sleep
import numpy as np
from enum import IntEnum
from struct import unpack, pack

DEBUG_CAN = False
USB_CAN_RX_FRAME_LENGTH = 16
USB_CAN_RX_HEADER = 0xAA
USB_CAN_RX_TAIL = 0x55
USB_CAN_RX_COMMAND = 0x11

class Control_Type(IntEnum):
    MIT = 1
    POS_VEL = 2  # 位置速度模式
    VEL = 3

class Motor:
    def __init__(self, MotorType, SlaveID, MasterID):
        self.state_q = 0.0
        self.state_dq = 0.0
        self.state_tau = 0.0
        self.SlaveID = SlaveID
        self.MasterID = MasterID
        self.MotorType = MotorType
        self.isEnable = False  # 记录电机反馈的使能状态
        self.error_code = 0
        self.mos_temperature_c = None
        self.rotor_temperature_c = None
        self.last_feedback_time = None
        self.NowControlMode = Control_Type.MIT
        self.temp_param_dict = {}

    def recv_data(
        self,
        q: float,
        dq: float,
        tau: float,
        status_code: int,
        mos_temperature_c: int,
        rotor_temperature_c: int,
    ):
        self.state_q = q
        self.state_dq = dq
        self.state_tau = tau
        self.error_code = status_code
        self.isEnable = status_code == 1
        self.mos_temperature_c = mos_temperature_c
        self.rotor_temperature_c = rotor_temperature_c
        self.last_feedback_time = monotonic()

class MotorControl:
    # 串口通讯帧头定义 (保持原样)
    send_data_frame = np.array(
        [0x55, 0xAA, 0x1e, 0x03, 0x01, 0x00, 0x00, 0x00, 0x0a, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0, 0x00, 0x08, 0x00,
         0x00, 0, 0, 0, 0, 0, 0, 0, 0, 0x00], np.uint8)
    
    Limit_Param = [[12.5, 30, 10], [12.5, 50, 10], [12.5, 8, 28], [12.5, 10, 28],
                   [12.5, 45, 20], [12.5, 45, 40], [12.5, 45, 54], [12.5, 25, 200], [12.5, 20, 200],
                   [12.5 , 280 , 1],[12.5 , 45 , 10],[12.5 , 45 , 10],
                   [12.5, 45, 10]]  # DM-S3519; verify PMAX/VMAX/TMAX on hardware.

    def __init__(self, serial_device):
        self.serial_ = serial_device
        self.motors_map = dict()
        self.recv_buffer = bytearray()
        if not self.serial_.is_open:
            self.serial_.open()

    def addMotor(self, Motor):
        self.motors_map[Motor.SlaveID] = Motor

    def switchControlMode(self, Motor, mode):
        """切换模式：向 0x7FF 写入寄存器 0x0A"""
        # 对应手册 p17: 写入参数 ID=0x7FF, RID=0x0A
        data = np.array([0]*8, np.uint8)
        data[0] = Motor.SlaveID & 0xFF
        data[1] = (Motor.SlaveID >> 8) & 0xFF
        data[2] = 0x55 # 写入标识
        data[3] = 0x0A # 寄存器地址: 控制模式
        data[4:8] = unpack('4B', pack('<I', int(mode))) # 写入模式值
        self.__send_data(0x7FF, data)
        Motor.NowControlMode = mode
        sleep(0.1) 

    def enable(self, Motor):
        """使能：发送 0xFC"""
        data = np.array([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFC], np.uint8)
        self.__send_data(Motor.SlaveID, data)
        sleep(0.05)

    def disable(self, Motor):
        """失能：发送 0xFD"""
        data = np.array([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFD], np.uint8)
        self.__send_data(Motor.SlaveID, data)

    def set_zero_position(self, Motor):
        """保存当前位置为零位"""
        data = np.array([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE], np.uint8)
        self.__send_data(Motor.SlaveID, data)

    def control_Pos_Vel(self, Motor, P_desired, V_desired):
        """位置速度模式：ID 偏移 0x100"""
        motorid = 0x100 + Motor.SlaveID # 手册 p9 规定
        data = np.array([0]*8, np.uint8)
        data[0:4] = unpack('4B', pack('<f', float(P_desired))) # 小端序浮点
        data[4:8] = unpack('4B', pack('<f', float(V_desired)))
        self.__send_data(motorid, data)
        self.recv()

    def control_Vel(self, Motor, V_desired):
        """速度模式：ID 偏移 0x200"""
        motorid = 0x200 + Motor.SlaveID
        data = np.array([0]*8, np.uint8)
        data[0:4] = unpack('4B', pack('<f', float(V_desired))) # 只发送速度
        self.__send_data(motorid, data)
        # Feedback is read by damiao_node's 100 Hz timer. Avoid blocking each
        # velocity command here so all four wheel commands, especially stop
        # commands, are sent with less skew.

    def recv(self):
        """Parse USB-CAN receive frames and update DM-S3519 feedback."""
        if self.serial_.in_waiting > 0:
            self.recv_buffer.extend(self.serial_.read(self.serial_.in_waiting))

        while len(self.recv_buffer) >= USB_CAN_RX_FRAME_LENGTH:
            if self.recv_buffer[0] != USB_CAN_RX_HEADER:
                del self.recv_buffer[0]
                continue

            if self.recv_buffer[USB_CAN_RX_FRAME_LENGTH - 1] != USB_CAN_RX_TAIL:
                del self.recv_buffer[0]
                continue

            frame = bytes(self.recv_buffer[:USB_CAN_RX_FRAME_LENGTH])
            del self.recv_buffer[:USB_CAN_RX_FRAME_LENGTH]
            self._process_receive_frame(frame)

    def _process_receive_frame(self, frame):
        """Decode one 16-byte USB-CAN receive frame."""
        if len(frame) != USB_CAN_RX_FRAME_LENGTH or frame[1] != USB_CAN_RX_COMMAND:
            return

        can_id = (
            frame[3]
            | (frame[4] << 8)
            | (frame[5] << 16)
            | (frame[6] << 24)
        )
        data = frame[7:15]

        # D0 low nibble is motor ID; D0 high nibble is status/error.
        payload_motor_id = data[0] & 0x0F
        target_id = can_id if can_id in self.motors_map else payload_motor_id
        motor = self.motors_map.get(target_id)
        if motor is None:
            if DEBUG_CAN:
                print(
                    f"[WARN] Motor ID {target_id} not in motors_map "
                    f"{list(self.motors_map.keys())}"
                )
            return

        status_code = (data[0] >> 4) & 0x0F
        q_uint = np.uint16((np.uint16(data[1]) << 8) | data[2])
        dq_uint = np.uint16((np.uint16(data[3]) << 4) | (data[4] >> 4))
        tau_uint = np.uint16(((data[4] & 0x0F) << 8) | data[5])
        limit = self.Limit_Param[motor.MotorType]
        q = self.__uint_to_float(q_uint, -limit[0], limit[0], 16)
        dq = self.__uint_to_float(dq_uint, -limit[1], limit[1], 12)
        tau = self.__uint_to_float(tau_uint, -limit[2], limit[2], 12)
        motor.recv_data(q, dq, tau, status_code, data[6], data[7])

        if DEBUG_CAN:
            data_hex = "".join(f"{byte:02X}" for byte in data)
            print(
                f"[DEBUG] can_id=0x{can_id:03X}, motor={target_id}, "
                f"status=0x{status_code:X}, q={q:.2f}, dq={dq:.2f}, "
                f"tau={tau:.2f}, mos={data[6]}C, rotor={data[7]}C, "
                f"data={data_hex}"
            )

    def __send_data(self, motor_id, data):
        self.send_data_frame[13] = motor_id & 0xff
        self.send_data_frame[14] = (motor_id >> 8)& 0xff
        self.send_data_frame[21:29] = data
        self.serial_.write(bytes(self.send_data_frame))

    def __uint_to_float(self, uint_value, min_value, max_value, bits):
        span = max_value - min_value
        offset = min_value
        return float(uint_value) * span / (float((1 << bits) - 1)) + offset

class DM_Motor_Type(IntEnum):
    DMS3519 = 12  # DM-S3519 geared motor with DM3520-1EC driver
