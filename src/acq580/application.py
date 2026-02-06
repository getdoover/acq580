"""ACQ580 VFD Application.

This application provides full monitoring and control of ABB ACQ580 variable
frequency drives via Modbus TCP communication.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional

from pydoover.docker import Application
from pydoover import ui

from .app_config import Acq580Config
from .app_ui import Acq580UI
from .app_state import Acq580State
from .modbus_client import ACQ580ModbusClient, DriveStatus, get_fault_description

log = logging.getLogger(__name__)


class Acq580Application(Application):
    """Doover application for ABB ACQ580 VFD monitoring and control.

    Features:
    - Real-time monitoring of all drive parameters
    - Remote start/stop and speed control
    - Alarm monitoring and notifications
    - State machine for safe operation sequencing
    - Data logging to channels
    """

    config: Acq580Config  # Type hint for IDE autocomplete
    loop_target_period = 2  # Poll every 2 seconds by default

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: Optional[Acq580UI] = None
        self.state: Optional[Acq580State] = None
        self.modbus_client: Optional[ACQ580ModbusClient] = None

        # Cached drive status
        self._last_status: Optional[DriveStatus] = None
        self._last_log_time: float = 0

        # Track alarm states to avoid repeated notifications
        self._alarm_states = {
            "high_current": False,
            "high_temp": False,
            "dc_bus_low": False,
            "dc_bus_high": False,
        }

    async def setup(self):
        """Initialize the application."""
        log.info("Setting up ACQ580 application")

        # Initialize UI
        self.ui = Acq580UI()
        self.ui_manager.add_children(*self.ui.fetch())

        # Set display name from config
        display_name = self.config.display_name.value
        self.ui_manager.set_display_name(display_name)

        # Initialize state machine
        self.state = Acq580State(app=self)

        # Initialize Modbus client with config
        modbus_cfg = self.config.modbus_connection
        self.modbus_client = ACQ580ModbusClient(
            host=modbus_cfg.elements[0].value,  # Host
            port=modbus_cfg.elements[1].value,  # Port
            unit_id=modbus_cfg.elements[2].value,  # Unit ID
            timeout=modbus_cfg.elements[3].value,  # Timeout
        )

        # Set loop period from config
        poll_interval = self.config.monitoring.elements[0].value
        self.loop_target_period = poll_interval

        log.info(f"ACQ580 configured: {modbus_cfg.elements[0].value}:{modbus_cfg.elements[1].value}")

    async def main_loop(self):
        """Main application loop - read status and update UI."""
        # Read drive status
        status = await self.modbus_client.read_status()
        self._last_status = status

        # Update state machine
        current_state = await self.state.spin_state(status)

        # Update connection status in UI
        self.ui.update_connection(
            connected=self.modbus_client.connected,
            error_count=self.modbus_client.error_count
        )

        if status:
            # Update UI with drive data
            self._update_ui_from_status(status)

            # Check alarm conditions
            await self._check_alarms(status)

            # Log data to channel if enabled
            if self.config.monitoring.elements[1].value:  # Log Data to Channel
                await self._log_drive_data(status)

            # Store state in tags for other apps to read
            await self._update_tags(status)
        else:
            # No status - show disconnected state
            self.ui.update_status(
                running=False,
                ready=False,
                fault=False,
                warning=False,
                state=current_state.upper()
            )

        log.debug(f"State: {current_state}, Connected: {self.modbus_client.connected}")

    def _update_ui_from_status(self, status: DriveStatus):
        """Update all UI elements from drive status."""
        # Update status section
        fault_desc = get_fault_description(status.fault_code) if status.fault else ""
        self.ui.update_status(
            running=status.running,
            ready=status.ready,
            fault=status.fault,
            warning=status.warning,
            state=status.state_description,
            fault_code=fault_desc
        )

        # Update output measurements
        self.ui.update_output(
            frequency=status.output_frequency,
            current=status.output_current,
            voltage=status.output_voltage,
            power=status.output_power,
            speed=status.motor_speed,
            torque=status.motor_torque
        )

        # Update power section
        self.ui.update_power_section(
            dc_voltage=status.dc_bus_voltage,
            temperature=status.drive_temperature,
            run_hours=status.run_hours,
            energy=status.energy_kwh
        )

        # Update setpoint display
        self.ui.update_setpoint(status.speed_reference)

    async def _check_alarms(self, status: DriveStatus):
        """Check alarm conditions and trigger notifications."""
        thresholds = self.config.alarm_thresholds
        rated_current = self.config.connected_load.elements[5].value  # Rated Current A

        # High current alarm
        current_percent = (status.output_current / rated_current * 100) if rated_current > 0 else 0
        high_current = current_percent > thresholds.elements[0].value
        await self._set_alarm("high_current", high_current,
                              f"High current: {status.output_current:.1f}A ({current_percent:.0f}%)")

        # High temperature alarm
        high_temp = status.drive_temperature > thresholds.elements[1].value
        await self._set_alarm("high_temp", high_temp,
                              f"High drive temperature: {status.drive_temperature:.1f}C")

        # DC bus voltage alarms
        dc_low = status.dc_bus_voltage < thresholds.elements[2].value
        dc_high = status.dc_bus_voltage > thresholds.elements[3].value
        await self._set_alarm("dc_bus_low", dc_low,
                              f"Low DC bus voltage: {status.dc_bus_voltage:.0f}V")
        await self._set_alarm("dc_bus_high", dc_high,
                              f"High DC bus voltage: {status.dc_bus_voltage:.0f}V")

        # Update UI alarm indicators
        self.ui.set_alarm("high_current", high_current)
        self.ui.set_alarm("high_temp", high_temp)
        self.ui.set_alarm("dc_bus", dc_low or dc_high)

    async def _set_alarm(self, alarm_name: str, active: bool, message: str):
        """Set alarm state and send notification on rising edge."""
        if active and not self._alarm_states.get(alarm_name, False):
            # Rising edge - send notification
            await self.ui.alerts.send_alert(message)
            log.warning(f"Alarm triggered: {message}")
        self._alarm_states[alarm_name] = active

    async def _log_drive_data(self, status: DriveStatus):
        """Log drive data to channel."""
        # Throttle logging (don't log more than once per second)
        now = time.time()
        if now - self._last_log_time < 1.0:
            return
        self._last_log_time = now

        load_cfg = self.config.connected_load
        data = {
            "timestamp": datetime.now().isoformat(),
            "load_name": load_cfg.elements[1].value,
            "load_type": load_cfg.elements[0].value,
            "state": status.state_description,
            "running": status.running,
            "ready": status.ready,
            "fault": status.fault,
            "fault_code": status.fault_code,
            "output_frequency_hz": status.output_frequency,
            "output_current_a": status.output_current,
            "output_voltage_v": status.output_voltage,
            "output_power_kw": status.output_power,
            "motor_speed_rpm": status.motor_speed,
            "motor_torque_pct": status.motor_torque,
            "dc_bus_voltage_v": status.dc_bus_voltage,
            "drive_temperature_c": status.drive_temperature,
            "run_hours": status.run_hours,
            "energy_kwh": status.energy_kwh,
            "speed_reference_hz": status.speed_reference,
        }

        await self.publish_to_channel("acq580_data", json.dumps(data))

    async def _update_tags(self, status: DriveStatus):
        """Update tags with current drive state."""
        await self.set_tag("running", status.running)
        await self.set_tag("ready", status.ready)
        await self.set_tag("fault", status.fault)
        await self.set_tag("output_frequency", status.output_frequency)
        await self.set_tag("output_current", status.output_current)
        await self.set_tag("output_power", status.output_power)
        await self.set_tag("motor_speed", status.motor_speed)
        await self.set_tag("state", self.state.state)

    # =========================================================================
    # UI Callbacks
    # =========================================================================

    @ui.callback("start_drive")
    async def on_start_drive(self, new_value):
        """Handle start drive button press."""
        if not self.config.control_enabled.value:
            log.warning("Control disabled - start command ignored")
            await self.ui.alerts.send_alert("Control disabled in configuration")
            self.ui.start_drive.coerce(None)
            return

        log.info("Start drive command received")
        self.state.request_start()
        self.ui.start_drive.coerce(None)

    @ui.callback("stop_drive")
    async def on_stop_drive(self, new_value):
        """Handle stop drive button press."""
        log.info("Stop drive command received")
        self.state.request_stop()
        self.ui.stop_drive.coerce(None)

    @ui.callback("fault_reset")
    async def on_fault_reset(self, new_value):
        """Handle fault reset button press."""
        log.info("Fault reset command received")
        self.state.request_fault_reset()
        if self.modbus_client:
            await self.modbus_client.reset_fault()
        self.ui.fault_reset.coerce(None)

    @ui.callback("emergency_stop")
    async def on_emergency_stop(self, new_value):
        """Handle emergency stop button press."""
        log.critical("Emergency stop command received!")
        self.state.request_emergency_stop()
        self.ui.emergency_stop.coerce(None)

    @ui.callback("speed_setpoint")
    async def on_speed_setpoint_change(self, new_value):
        """Handle speed setpoint parameter change."""
        if not self.config.control_enabled.value:
            log.warning("Control disabled - setpoint change ignored")
            return

        if new_value is None:
            return

        try:
            frequency = float(new_value)
            # Clamp to configured limits
            max_freq = self.config.operating_params.elements[0].value
            min_freq = self.config.operating_params.elements[1].value
            frequency = max(min_freq, min(frequency, max_freq))

            log.info(f"Setting speed reference to {frequency:.1f} Hz")
            if self.modbus_client:
                await self.modbus_client.set_speed_reference(frequency)
        except (ValueError, TypeError) as e:
            log.error(f"Invalid setpoint value: {new_value} - {e}")

    @ui.callback("control_mode")
    async def on_control_mode_change(self, new_value):
        """Handle control mode state command change."""
        log.info(f"Control mode changed to: {new_value}")
        # Note: Control mode changes may need to be sent to the drive
        # depending on the specific drive configuration
