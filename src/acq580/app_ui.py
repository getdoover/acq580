from datetime import datetime
from pydoover import ui


class Acq580UI:
    """UI components for the ACQ580 VFD application.

    Provides:
    - Drive status monitoring (running state, frequency, current, etc.)
    - Control actions (start, stop, speed setpoint)
    - Alarm indicators
    - Historical data visualization
    """

    def __init__(self):
        # ============================================================
        # Drive Status Variables
        # ============================================================
        self.drive_status = ui.Submodule("drive_status", "Drive Status")

        self.running = ui.BooleanVariable("running", "Running")
        self.ready = ui.BooleanVariable("ready", "Ready")
        self.fault = ui.BooleanVariable("fault", "Fault Active")
        self.warning = ui.BooleanVariable("warning", "Warning Active")

        self.drive_state = ui.TextVariable("drive_state", "Drive State")
        self.fault_code = ui.TextVariable("fault_code", "Fault Code")

        self.drive_status.add_children(
            self.running, self.ready, self.fault, self.warning,
            self.drive_state, self.fault_code
        )

        # ============================================================
        # Output Measurements
        # ============================================================
        self.output = ui.Submodule("output", "Output Measurements")

        self.output_frequency = ui.NumericVariable(
            "output_frequency", "Output Frequency",
            precision=1, unit="Hz",
            ranges=[
                ui.Range("Low", 0, 10, ui.Colour.yellow),
                ui.Range("Normal", 10, 50, ui.Colour.green),
                ui.Range("High", 50, 60, ui.Colour.red),
            ]
        )
        self.output_current = ui.NumericVariable(
            "output_current", "Output Current",
            precision=1, unit="A",
            ranges=[
                ui.Range("Normal", 0, 80, ui.Colour.green),
                ui.Range("High", 80, 100, ui.Colour.yellow),
                ui.Range("Critical", 100, 150, ui.Colour.red),
            ]
        )
        self.output_voltage = ui.NumericVariable(
            "output_voltage", "Output Voltage",
            precision=0, unit="V"
        )
        self.output_power = ui.NumericVariable(
            "output_power", "Output Power",
            precision=1, unit="kW"
        )
        self.motor_speed = ui.NumericVariable(
            "motor_speed", "Motor Speed",
            precision=0, unit="RPM"
        )
        self.motor_torque = ui.NumericVariable(
            "motor_torque", "Motor Torque",
            precision=1, unit="%"
        )

        self.output.add_children(
            self.output_frequency, self.output_current, self.output_voltage,
            self.output_power, self.motor_speed, self.motor_torque
        )

        # ============================================================
        # DC Bus and Temperatures
        # ============================================================
        self.power_section = ui.Submodule("power_section", "Power Section")

        self.dc_bus_voltage = ui.NumericVariable(
            "dc_bus_voltage", "DC Bus Voltage",
            precision=0, unit="V",
            ranges=[
                ui.Range("Low", 0, 500, ui.Colour.yellow),
                ui.Range("Normal", 500, 750, ui.Colour.green),
                ui.Range("High", 750, 900, ui.Colour.red),
            ]
        )
        self.drive_temperature = ui.NumericVariable(
            "drive_temperature", "Drive Temperature",
            precision=1, unit="C",
            ranges=[
                ui.Range("Cool", 0, 40, ui.Colour.green),
                ui.Range("Warm", 40, 70, ui.Colour.yellow),
                ui.Range("Hot", 70, 100, ui.Colour.red),
            ]
        )
        self.run_hours = ui.NumericVariable(
            "run_hours", "Run Hours",
            precision=0, unit="hrs"
        )
        self.energy_kwh = ui.NumericVariable(
            "energy_kwh", "Energy Consumed",
            precision=1, unit="kWh"
        )

        self.power_section.add_children(
            self.dc_bus_voltage, self.drive_temperature,
            self.run_hours, self.energy_kwh
        )

        # ============================================================
        # Control Section
        # ============================================================
        self.control = ui.Submodule("control", "Control")

        self.speed_setpoint = ui.NumericParameter(
            "speed_setpoint", "Speed Setpoint",
            precision=1
        )
        self.speed_setpoint_display = ui.NumericVariable(
            "speed_setpoint_display", "Active Setpoint",
            precision=1, unit="Hz"
        )

        self.control_mode = ui.StateCommand(
            "control_mode", "Control Mode",
            user_options=[
                ui.Option("remote", "Remote"),
                ui.Option("local", "Local Panel"),
            ]
        )

        self.start_drive = ui.Action(
            "start_drive", "Start Drive",
            colour=ui.Colour.green,
            position=1
        )
        self.stop_drive = ui.Action(
            "stop_drive", "Stop Drive",
            colour=ui.Colour.red,
            position=2
        )
        self.fault_reset = ui.Action(
            "fault_reset", "Reset Fault",
            colour=ui.Colour.yellow,
            requires_confirm=True,
            position=3
        )
        self.emergency_stop = ui.Action(
            "emergency_stop", "Emergency Stop",
            colour=ui.Colour.red,
            requires_confirm=True,
            position=4
        )

        self.control.add_children(
            self.speed_setpoint, self.speed_setpoint_display,
            self.control_mode,
            self.start_drive, self.stop_drive, self.fault_reset, self.emergency_stop
        )

        # ============================================================
        # Alarms and Warnings
        # ============================================================
        self.alarms = ui.Submodule("alarms", "Alarms")

        self.high_current_alarm = ui.WarningIndicator(
            "high_current_alarm", "High Current",
            hidden=True
        )
        self.high_temp_alarm = ui.WarningIndicator(
            "high_temp_alarm", "High Temperature",
            hidden=True
        )
        self.dc_bus_alarm = ui.WarningIndicator(
            "dc_bus_alarm", "DC Bus Voltage",
            hidden=True
        )
        self.comms_alarm = ui.WarningIndicator(
            "comms_alarm", "Communication Lost",
            hidden=True
        )

        self.alarms.add_children(
            self.high_current_alarm, self.high_temp_alarm,
            self.dc_bus_alarm, self.comms_alarm
        )

        # ============================================================
        # Connection Status
        # ============================================================
        self.connection = ui.Submodule("connection", "Connection")

        self.connected = ui.BooleanVariable("connected", "Connected")
        self.last_update = ui.DateTimeVariable("last_update", "Last Update")
        self.comms_errors = ui.NumericVariable(
            "comms_errors", "Comm Errors",
            precision=0
        )

        self.connection.add_children(
            self.connected, self.last_update, self.comms_errors
        )

        # ============================================================
        # Alert Stream for notifications
        # ============================================================
        self.alerts = ui.AlertStream()

    def fetch(self):
        """Return all top-level UI components for registration."""
        return (
            self.drive_status,
            self.output,
            self.power_section,
            self.control,
            self.alarms,
            self.connection,
            self.alerts
        )

    def update_status(self, running: bool, ready: bool, fault: bool, warning: bool,
                      state: str, fault_code: str = ""):
        """Update drive status variables."""
        self.running.update(running)
        self.ready.update(ready)
        self.fault.update(fault)
        self.warning.update(warning)
        self.drive_state.update(state)
        self.fault_code.update(fault_code if fault_code else "None")

    def update_output(self, frequency: float, current: float, voltage: float,
                      power: float, speed: float, torque: float):
        """Update output measurement variables."""
        self.output_frequency.update(frequency)
        self.output_current.update(current)
        self.output_voltage.update(voltage)
        self.output_power.update(power)
        self.motor_speed.update(speed)
        self.motor_torque.update(torque)

    def update_power_section(self, dc_voltage: float, temperature: float,
                             run_hours: float, energy: float):
        """Update power section variables."""
        self.dc_bus_voltage.update(dc_voltage)
        self.drive_temperature.update(temperature)
        self.run_hours.update(run_hours)
        self.energy_kwh.update(energy)

    def update_setpoint(self, setpoint: float):
        """Update the active speed setpoint display."""
        self.speed_setpoint_display.update(setpoint)

    def update_connection(self, connected: bool, error_count: int):
        """Update connection status."""
        self.connected.update(connected)
        self.last_update.update(datetime.now())
        self.comms_errors.update(error_count)

    def set_alarm(self, alarm_name: str, active: bool):
        """Show or hide an alarm indicator."""
        alarm_map = {
            "high_current": self.high_current_alarm,
            "high_temp": self.high_temp_alarm,
            "dc_bus": self.dc_bus_alarm,
            "comms": self.comms_alarm,
        }
        if alarm_name in alarm_map:
            alarm_map[alarm_name].hidden = not active

    def clear_all_alarms(self):
        """Hide all alarm indicators."""
        self.high_current_alarm.hidden = True
        self.high_temp_alarm.hidden = True
        self.dc_bus_alarm.hidden = True
        self.comms_alarm.hidden = True
