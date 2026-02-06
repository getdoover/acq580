from pathlib import Path

from pydoover import config


class Acq580Config(config.Schema):
    """Configuration schema for the ACQ580 VFD application.

    Allows users to configure:
    - Modbus connection parameters
    - Connected load information
    - Monitoring and control parameters
    """

    def __init__(self):
        # Display name for the drive instance
        self.display_name = config.String(
            "Display Name",
            description="Name to display for this drive instance",
            default="ACQ580 Drive"
        )

        # Modbus Connection Configuration
        self.modbus_connection = config.Object("Modbus Connection")
        self.modbus_connection.add_elements(
            config.String(
                "Host",
                description="IP address or hostname of the Modbus gateway/drive",
                default="192.168.1.100"
            ),
            config.Integer(
                "Port",
                description="Modbus TCP port",
                default=502
            ),
            config.Integer(
                "Unit ID",
                description="Modbus unit/slave ID (1-247)",
                default=1
            ),
            config.Number(
                "Timeout",
                description="Communication timeout in seconds",
                default=3.0
            )
        )

        # Connected Load Configuration
        self.connected_load = config.Object("Connected Load")
        self.connected_load.add_elements(
            config.String(
                "Load Type",
                description="Type of load connected (e.g., Pump, Fan, Conveyor, Compressor)",
                default="Pump"
            ),
            config.String(
                "Load Name",
                description="Name/identifier for the connected load",
                default="Main Pump"
            ),
            config.Number(
                "Rated Power kW",
                description="Rated power of the connected motor in kW",
                default=11.0
            ),
            config.Number(
                "Rated Speed RPM",
                description="Rated speed of the connected motor in RPM",
                default=1450.0
            ),
            config.Number(
                "Rated Voltage V",
                description="Rated voltage of the connected motor in Volts",
                default=400.0
            ),
            config.Number(
                "Rated Current A",
                description="Rated current of the connected motor in Amps",
                default=22.0
            )
        )

        # Operating Parameters
        self.operating_params = config.Object("Operating Parameters")
        self.operating_params.add_elements(
            config.Number(
                "Max Frequency Hz",
                description="Maximum output frequency limit in Hz",
                default=50.0
            ),
            config.Number(
                "Min Frequency Hz",
                description="Minimum output frequency limit in Hz",
                default=0.0
            ),
            config.Number(
                "Accel Time s",
                description="Acceleration time in seconds (0 to max freq)",
                default=10.0
            ),
            config.Number(
                "Decel Time s",
                description="Deceleration time in seconds (max freq to 0)",
                default=10.0
            )
        )

        # Monitoring Configuration
        self.monitoring = config.Object("Monitoring")
        self.monitoring.add_elements(
            config.Number(
                "Poll Interval s",
                description="How often to poll drive status (seconds)",
                default=2.0
            ),
            config.Boolean(
                "Log Data to Channel",
                description="Enable logging of drive data to a channel",
                default=True
            )
        )

        # Alarm Thresholds
        self.alarm_thresholds = config.Object("Alarm Thresholds")
        self.alarm_thresholds.add_elements(
            config.Number(
                "High Current %",
                description="Alarm when current exceeds this % of rated",
                default=90.0
            ),
            config.Number(
                "High Temperature C",
                description="Alarm when drive temperature exceeds this (Celsius)",
                default=70.0
            ),
            config.Number(
                "Low DC Bus V",
                description="Alarm when DC bus voltage drops below this",
                default=500.0
            ),
            config.Number(
                "High DC Bus V",
                description="Alarm when DC bus voltage exceeds this",
                default=750.0
            )
        )

        # Control Permissions
        self.control_enabled = config.Boolean(
            "Control Enabled",
            description="Allow remote start/stop and speed control commands",
            default=True
        )


def export():
    """Export configuration schema to doover_config.json."""
    Acq580Config().export(Path(__file__).parents[2] / "doover_config.json", "acq580")


if __name__ == "__main__":
    export()
