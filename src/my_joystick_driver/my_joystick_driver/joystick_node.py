#!/usr/bin/env python3
import threading
import time
import rclpy
from rclpy.node import Node
from my_joystick_msgs.msg import Joystick
from evdev import InputDevice, ecodes, list_devices

AXIS_MAX = 512
DEADZONE = 15  # 15 / 512 = 2.93%
SUPPORTED_DEVICE_NAMES = {
    '8BitDo Ultimate Wireless / Pro 2 Wired Controller',
    'Generic X-Box pad',
}


class JoystickPublisher(Node):
    def __init__(self):
        super().__init__('joystick_node')

        # Declare ROS2 parameters for flexible configuration
        self.declare_parameter('auto_detect', True)
        self.declare_parameter('device_path', '')
        self.declare_parameter('device_name_filter', '8BitDo')
        
        self.auto_detect = self.get_parameter('auto_detect').get_parameter_value().bool_value
        self.device_path = self.get_parameter('device_path').get_parameter_value().string_value
        self.device_name_filter = self.get_parameter('device_name_filter').get_parameter_value().string_value

        self.publisher_ = self.create_publisher(Joystick, 'joystick_data', 10)
        self.get_logger().info("Joystick publisher node initialized")
        self.get_logger().info(f"Configuration: auto_detect={self.auto_detect}, device_path='{self.device_path}', filter='{self.device_name_filter}'")

        self.button_states = {
            "a": False, "b": False, "x": False, "y": False,
            "l1": False, "r1": False, "l3": False, "r3": False,
            "select": False, "start": False,
        }

        self.axis_states = {
            "lx": 0, "ly": 0, "rx": 0, "ry": 0,
            "dx": 0, "dy": 0, "l2": 0, "r2": 0,
        }

        # Axis normalization parameters (raw min/max -> -512 to 512)
        # Adjust these based on your controller's calibration
        self.axis_ranges = {
            "lx": (-32768, 32767),
            "ly": (-32768, 32767),
            "rx": (-32768, 32767),
            "ry": (-32768, 32767),
            "dx": (-1, 1),  # D-pad is typically -1, 0, 1
            "dy": (-1, 1),
            "l2": (0, 255),  # Triggers are typically 0 to 255
            "r2": (0, 255),
        }

        # Deadzone threshold to filter out small drift near center
        self.deadzone = DEADZONE

        self.button_mapping = {
            ecodes.BTN_SOUTH: "a",
            ecodes.BTN_EAST: "b",
            ecodes.BTN_WEST: "y",
            ecodes.BTN_NORTH: "x",
            ecodes.BTN_TL: "l1",
            ecodes.BTN_TR: "r1",
            ecodes.BTN_THUMBL: "l3",
            ecodes.BTN_THUMBR: "r3",
            ecodes.BTN_SELECT: "select",
            ecodes.BTN_START: "start",
        }

        self.axis_mapping = {
            ecodes.ABS_X: "lx",
            ecodes.ABS_Y: "ly",
            ecodes.ABS_RX: "rx",
            ecodes.ABS_RY: "ry",
            ecodes.ABS_HAT0X: "dx",
            ecodes.ABS_HAT0Y: "dy",
            ecodes.ABS_Z: "l2",
            ecodes.ABS_RZ: "r2",
        }

        self.running = True
        self.gamepad = None

        self._reset_states()

        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

        self.publish_timer = self.create_timer(0.05, self._publish_current_state)

    def _reset_states(self):
        """Reset all button and axis states to default (safe) values"""
        for btn in self.button_states:
            self.button_states[btn] = False
        for axis in self.axis_states:
            self.axis_states[axis] = 0
        self.get_logger().info("Joystick states reset to safety (all zeros)")

    def _normalize_axis(self, axis_name, raw_value):
        """Normalize raw axis value to -512 ~ 512 range with deadzone."""
        min_val, max_val = self.axis_ranges[axis_name]
        
        # Special handling for triggers (0 to 512 instead of -512 to 512)
        if axis_name in ["l2", "r2"]:
            normalized = int((raw_value - min_val) / (max_val - min_val) * AXIS_MAX)
            # Apply deadzone for triggers
            if normalized < self.deadzone:
                return 0
            return normalized
        
        # Standard normalization for joysticks and D-pad
        mid = (min_val + max_val) / 2.0
        range_half = (max_val - min_val) / 2.0
        normalized = int((raw_value - mid) / range_half * AXIS_MAX)
        
        # Apply deadzone - ignore small values near center
        if abs(normalized) < self.deadzone:
            return 0
        
        return normalized

    @staticmethod
    def _is_supported_device_name(device_name, name_filter):
        """Match confirmed controllers or a caller-provided name filter."""
        return (
            device_name in SUPPORTED_DEVICE_NAMES
            or bool(name_filter and name_filter in device_name)
        )

    def _find_8bitdo_device(self):
        """Find a confirmed controller or a device matching the configured filter."""
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if self._is_supported_device_name(device.name, self.device_name_filter):
                return device
        return None
    
    def _print_available_devices(self):
        """Log all available input devices for debugging"""
        self.get_logger().info("=== Available Input Devices ===")
        devices = [InputDevice(path) for path in list_devices()]
        if not devices:
            self.get_logger().warn("No input devices found!")
        for dev in devices:
            self.get_logger().info(f"  Path: {dev.path}")
            self.get_logger().info(f"  Name: {dev.name}")
            self.get_logger().info(f"  Phys: {dev.phys}")
            self.get_logger().info(f"  ---")
        self.get_logger().info("===============================")

    def _try_connect(self):
        """Attempt to connect to the joystick device"""
        try:
            if self.auto_detect:
                # Auto-detect mode: search by name filter
                self.gamepad = self._find_8bitdo_device()
                if self.gamepad:
                    self.get_logger().info(f"Auto-detected device: {self.gamepad.name}")
                    return True
                else:
                    self.get_logger().warn(f"No device found with filter '{self.device_name_filter}'. Retrying...")
                    self._print_available_devices()
                    return False
            else:
                # Manual mode: use specified device path
                self.gamepad = InputDevice(self.device_path)
                self.get_logger().info(f"Connected to device at {self.device_path}: {self.gamepad.name}")
                return True
        except FileNotFoundError:
            self.get_logger().error(f"Device not found at {self.device_path}")
            self._print_available_devices()
            return False
        except PermissionError:
            self.get_logger().error("Permission denied. Add your user to 'input' group.")
            return False
        except Exception as e:
            self.get_logger().error(f"Failed to connect to joystick: {e}")
            return False

    def _read_loop(self):
        """Background thread: continuously read joystick events"""
        while self.running and rclpy.ok():
            if self.gamepad is None:
                if not self._try_connect():
                    time.sleep(1)
                    continue

            try:
                for event in self.gamepad.read_loop():
                    if not self.running or not rclpy.ok():
                        break

                    if event.type == ecodes.EV_KEY:
                        btn = self.button_mapping.get(event.code)
                        if btn is not None:
                            self.button_states[btn] = (event.value == 1)
                    elif event.type == ecodes.EV_ABS:
                        axis = self.axis_mapping.get(event.code)
                        if axis is not None:
                            self.axis_states[axis] = self._normalize_axis(axis, event.value)
            except OSError as e:
                self.get_logger().error(f"Joystick OSError: {e}. Device may be disconnected.")
                if self.gamepad:
                    self.gamepad.close()
                    self.gamepad = None
                # Reset to safe state immediately upon disconnection
                self._reset_states()
                time.sleep(2)
            except Exception as e:
                self.get_logger().error(f"Unexpected error: {e}")
                if self.gamepad:
                    self.gamepad.close()
                    self.gamepad = None
                time.sleep(2)

        if self.gamepad:
            self.gamepad.close()
            self.get_logger().info("Joystick device closed.")

    def _publish_current_state(self):
        """Publish the latest axis/button states"""
        msg = Joystick()

        msg.lx = self.axis_states['lx']
        msg.ly = self.axis_states['ly']
        msg.rx = self.axis_states['rx']
        msg.ry = self.axis_states['ry']
        msg.dx = self.axis_states['dx']
        msg.dy = self.axis_states['dy']
        msg.l2 = self.axis_states['l2']
        msg.r2 = self.axis_states['r2']

        msg.a = self.button_states['a']
        msg.b = self.button_states['b']
        msg.x = self.button_states['x']
        msg.y = self.button_states['y']
        msg.l1 = self.button_states['l1']
        msg.r1 = self.button_states['r1']
        msg.l3 = self.button_states['l3']
        msg.r3 = self.button_states['r3']
        msg.select = self.button_states['select']
        msg.start = self.button_states['start']

        self.publisher_.publish(msg)

    def destroy_node(self):
        """Clean up resources"""
        self.running = False
        if hasattr(self, 'publish_timer'):
            self.publish_timer.cancel()
        if self.gamepad:
            self.gamepad.close()
        # Reset to safe state on shutdown
        self._reset_states()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    joystick_publisher = JoystickPublisher()

    try:
        rclpy.spin(joystick_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        if joystick_publisher is not None:
            joystick_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
