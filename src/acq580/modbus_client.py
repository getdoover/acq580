"""Modbus client for ABB ACQ580 VFD communication.

This module provides a high-level interface to the ACQ580 drive's Modbus registers.
The ACQ580 uses standard ABB Modbus register mapping.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

log = logging.getLogger(__name__)


# ==============================================================================
# ACQ580 Modbus Register Definitions
# Based on ABB ACQ580 Modbus Communication User Manual
# ==============================================================================

# Status Word Register (read-only)
REG_STATUS_WORD = 1  # Holding register 1 (0-indexed: 0)

# Control Word Register (read/write)
REG_CONTROL_WORD = 0  # Holding register 0

# Reference/Setpoint Register (read/write)
REG_REFERENCE = 2  # Speed reference (0.01 Hz resolution)

# Actual Values (read-only) - Holding registers
REG_OUTPUT_FREQUENCY = 3      # Output frequency (0.01 Hz)
REG_OUTPUT_CURRENT = 4        # Output current (0.1 A)
REG_OUTPUT_VOLTAGE = 5        # Output voltage (0.1 V)
REG_OUTPUT_POWER = 6          # Output power (0.1 kW)
REG_MOTOR_SPEED = 7           # Motor speed (1 RPM)
REG_MOTOR_TORQUE = 8          # Motor torque (0.1 %)
REG_DC_BUS_VOLTAGE = 9        # DC bus voltage (1 V)
REG_DRIVE_TEMPERATURE = 10    # Drive temperature (0.1 C)
REG_RUN_HOURS = 11            # Run hours (1 h)
REG_ENERGY_KWH = 12           # Energy counter (0.1 kWh)

# Fault/Warning Registers
REG_FAULT_CODE = 50           # Last fault code
REG_WARNING_CODE = 51         # Active warning code

# Control Word Bits
CW_BIT_RUN = 0                # Bit 0: Run/Stop
CW_BIT_DIRECTION = 1          # Bit 1: Direction (0=Forward, 1=Reverse)
CW_BIT_FAULT_RESET = 2        # Bit 2: Fault reset
CW_BIT_EMERGENCY_STOP = 3     # Bit 3: Emergency stop (0=Normal, 1=E-Stop)
CW_BIT_REMOTE = 4             # Bit 4: Remote control (1=Remote, 0=Local)

# Status Word Bits
SW_BIT_READY = 0              # Bit 0: Ready to run
SW_BIT_RUNNING = 1            # Bit 1: Drive running
SW_BIT_DIRECTION = 2          # Bit 2: Current direction
SW_BIT_FAULT = 3              # Bit 3: Fault active
SW_BIT_WARNING = 4            # Bit 4: Warning active
SW_BIT_AT_REFERENCE = 5       # Bit 5: At reference speed
SW_BIT_REMOTE = 6             # Bit 6: Remote control active


@dataclass
class DriveStatus:
    """Data class containing drive status information."""
    ready: bool = False
    running: bool = False
    direction_forward: bool = True
    fault: bool = False
    warning: bool = False
    at_reference: bool = False
    remote_control: bool = False

    # Measurements
    output_frequency: float = 0.0
    output_current: float = 0.0
    output_voltage: float = 0.0
    output_power: float = 0.0
    motor_speed: float = 0.0
    motor_torque: float = 0.0
    dc_bus_voltage: float = 0.0
    drive_temperature: float = 0.0
    run_hours: float = 0.0
    energy_kwh: float = 0.0

    # Faults
    fault_code: int = 0
    warning_code: int = 0

    # Reference
    speed_reference: float = 0.0

    @property
    def state_description(self) -> str:
        """Return a human-readable state description."""
        if self.fault:
            return f"FAULT ({self.fault_code})"
        if not self.ready:
            return "NOT READY"
        if self.running:
            if self.at_reference:
                return "RUNNING"
            return "ACCELERATING"
        return "READY"


class ACQ580ModbusClient:
    """Async Modbus client for ABB ACQ580 VFD."""

    def __init__(self, host: str, port: int = 502, unit_id: int = 1, timeout: float = 3.0):
        """Initialize the Modbus client.

        Args:
            host: IP address or hostname of the Modbus gateway/drive
            port: Modbus TCP port (default 502)
            unit_id: Modbus unit/slave ID (default 1)
            timeout: Communication timeout in seconds
        """
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: Optional[AsyncModbusTcpClient] = None
        self._connected = False
        self._error_count = 0

    @property
    def connected(self) -> bool:
        """Return True if connected to the drive."""
        return self._connected and self._client is not None

    @property
    def error_count(self) -> int:
        """Return the number of communication errors."""
        return self._error_count

    async def connect(self) -> bool:
        """Connect to the Modbus device.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            self._connected = await self._client.connect()
            if self._connected:
                log.info(f"Connected to ACQ580 at {self.host}:{self.port}")
            else:
                log.warning(f"Failed to connect to ACQ580 at {self.host}:{self.port}")
            return self._connected
        except Exception as e:
            log.error(f"Connection error: {e}")
            self._connected = False
            self._error_count += 1
            return False

    async def disconnect(self):
        """Disconnect from the Modbus device."""
        if self._client:
            self._client.close()
            self._client = None
        self._connected = False
        log.info("Disconnected from ACQ580")

    async def read_status(self) -> Optional[DriveStatus]:
        """Read all status registers from the drive.

        Returns:
            DriveStatus object or None if read failed
        """
        if not self.connected:
            if not await self.connect():
                return None

        try:
            # Read status word and measurements in one batch (registers 0-15)
            result = await self._client.read_holding_registers(
                address=0,
                count=16,
                slave=self.unit_id
            )

            if result.isError():
                log.error(f"Error reading status registers: {result}")
                self._error_count += 1
                return None

            # Parse status word
            status_word = result.registers[REG_STATUS_WORD]
            status = DriveStatus(
                ready=bool(status_word & (1 << SW_BIT_READY)),
                running=bool(status_word & (1 << SW_BIT_RUNNING)),
                direction_forward=not bool(status_word & (1 << SW_BIT_DIRECTION)),
                fault=bool(status_word & (1 << SW_BIT_FAULT)),
                warning=bool(status_word & (1 << SW_BIT_WARNING)),
                at_reference=bool(status_word & (1 << SW_BIT_AT_REFERENCE)),
                remote_control=bool(status_word & (1 << SW_BIT_REMOTE)),
            )

            # Parse reference
            status.speed_reference = result.registers[REG_REFERENCE] / 100.0

            # Parse measurements
            status.output_frequency = result.registers[REG_OUTPUT_FREQUENCY] / 100.0
            status.output_current = result.registers[REG_OUTPUT_CURRENT] / 10.0
            status.output_voltage = result.registers[REG_OUTPUT_VOLTAGE] / 10.0
            status.output_power = result.registers[REG_OUTPUT_POWER] / 10.0
            status.motor_speed = result.registers[REG_MOTOR_SPEED]
            status.motor_torque = result.registers[REG_MOTOR_TORQUE] / 10.0
            status.dc_bus_voltage = result.registers[REG_DC_BUS_VOLTAGE]
            status.drive_temperature = result.registers[REG_DRIVE_TEMPERATURE] / 10.0
            status.run_hours = result.registers[REG_RUN_HOURS]
            status.energy_kwh = result.registers[REG_ENERGY_KWH] / 10.0

            # Read fault/warning codes separately
            fault_result = await self._client.read_holding_registers(
                address=REG_FAULT_CODE,
                count=2,
                slave=self.unit_id
            )
            if not fault_result.isError():
                status.fault_code = fault_result.registers[0]
                status.warning_code = fault_result.registers[1]

            return status

        except ModbusException as e:
            log.error(f"Modbus exception reading status: {e}")
            self._error_count += 1
            self._connected = False
            return None
        except Exception as e:
            log.error(f"Error reading status: {e}")
            self._error_count += 1
            return None

    async def write_control_word(self, run: bool = None, direction_forward: bool = None,
                                  fault_reset: bool = False, emergency_stop: bool = False,
                                  remote: bool = True) -> bool:
        """Write the control word to the drive.

        Args:
            run: True to run, False to stop, None to maintain current state
            direction_forward: True for forward, False for reverse
            fault_reset: True to reset fault
            emergency_stop: True to activate emergency stop
            remote: True for remote control, False for local

        Returns:
            True if write successful
        """
        if not self.connected:
            if not await self.connect():
                return False

        try:
            # Build control word
            control_word = 0

            if run is True:
                control_word |= (1 << CW_BIT_RUN)

            if direction_forward is False:
                control_word |= (1 << CW_BIT_DIRECTION)

            if fault_reset:
                control_word |= (1 << CW_BIT_FAULT_RESET)

            if emergency_stop:
                control_word |= (1 << CW_BIT_EMERGENCY_STOP)

            if remote:
                control_word |= (1 << CW_BIT_REMOTE)

            result = await self._client.write_register(
                address=REG_CONTROL_WORD,
                value=control_word,
                slave=self.unit_id
            )

            if result.isError():
                log.error(f"Error writing control word: {result}")
                self._error_count += 1
                return False

            log.debug(f"Control word written: {control_word:#06x}")
            return True

        except ModbusException as e:
            log.error(f"Modbus exception writing control: {e}")
            self._error_count += 1
            self._connected = False
            return False
        except Exception as e:
            log.error(f"Error writing control: {e}")
            self._error_count += 1
            return False

    async def set_speed_reference(self, frequency_hz: float) -> bool:
        """Set the speed reference in Hz.

        Args:
            frequency_hz: Target frequency in Hz (0.01 Hz resolution)

        Returns:
            True if write successful
        """
        if not self.connected:
            if not await self.connect():
                return False

        try:
            # Convert to register value (0.01 Hz units)
            ref_value = int(frequency_hz * 100)
            ref_value = max(0, min(ref_value, 65535))  # Clamp to valid range

            result = await self._client.write_register(
                address=REG_REFERENCE,
                value=ref_value,
                slave=self.unit_id
            )

            if result.isError():
                log.error(f"Error writing speed reference: {result}")
                self._error_count += 1
                return False

            log.debug(f"Speed reference set to {frequency_hz:.2f} Hz")
            return True

        except ModbusException as e:
            log.error(f"Modbus exception writing reference: {e}")
            self._error_count += 1
            self._connected = False
            return False
        except Exception as e:
            log.error(f"Error writing reference: {e}")
            self._error_count += 1
            return False

    async def start(self) -> bool:
        """Start the drive."""
        log.info("Starting drive")
        return await self.write_control_word(run=True, remote=True)

    async def stop(self) -> bool:
        """Stop the drive (normal stop)."""
        log.info("Stopping drive")
        return await self.write_control_word(run=False, remote=True)

    async def emergency_stop(self) -> bool:
        """Emergency stop the drive."""
        log.warning("Emergency stop activated!")
        return await self.write_control_word(run=False, emergency_stop=True, remote=True)

    async def reset_fault(self) -> bool:
        """Reset drive fault."""
        log.info("Resetting fault")
        # Send fault reset pulse
        success = await self.write_control_word(fault_reset=True, remote=True)
        if success:
            # Clear fault reset bit
            await self.write_control_word(fault_reset=False, remote=True)
        return success


# Fault code descriptions for ABB ACQ580
FAULT_CODES = {
    0: "No fault",
    1: "Overcurrent",
    2: "DC overvoltage",
    3: "Device overtemperature",
    4: "Short circuit",
    5: "IGBT overtemperature",
    6: "Ground fault",
    7: "DC undervoltage",
    8: "Motor overtemperature",
    9: "Output phase supervision",
    10: "Encoder fault",
    11: "External fault 1",
    12: "External fault 2",
    13: "Panel loss",
    14: "Parameter fault",
    15: "Safe torque off",
    16: "Supply phase loss",
    17: "Motor stall",
    18: "Underload",
    19: "Overspeed",
    20: "PID supervision",
    21: "Drive overload",
    22: "Motor overload",
    23: "Communication loss",
    # Add more as needed
}


def get_fault_description(fault_code: int) -> str:
    """Get a human-readable description for a fault code."""
    return FAULT_CODES.get(fault_code, f"Unknown fault ({fault_code})")
