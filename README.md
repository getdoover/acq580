# ACQ580

<img src="https://cdn.worldvectorlogo.com/logos/abb-1.svg" alt="ABB Logo" style="max-width: 100px;">

**Full monitoring and control of ABB ACQ580 variable frequency drives via Modbus TCP**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/getdoover/acq580)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/acq580/blob/main/LICENSE)

[Getting Started](#getting-started) | [Configuration](#configuration) | [Developer](https://github.com/getdoover/acq580/blob/main/DEVELOPMENT.md) | [Need Help?](#need-help)

<br/>

## Overview

The ACQ580 app enables a Doovit device to interface with ABB ACQ580 variable frequency drives (VFDs) over Modbus TCP. This application provides comprehensive real-time monitoring of all drive parameters and full remote control capabilities, making it ideal for water and wastewater applications where the ACQ580 is commonly deployed.

With this application, operators can monitor drive status, output measurements (frequency, current, voltage, power), motor parameters (speed, torque), and internal diagnostics (DC bus voltage, temperature, run hours, energy consumption) - all from a single unified interface. The application implements a robust state machine for safe operation sequencing and includes configurable alarm thresholds with automatic notifications.

The connected load configuration allows users to document exactly what equipment is being driven - whether a pump, fan, conveyor, compressor, or other machinery - complete with nameplate data that enables intelligent alarm calculations based on percentage of rated values rather than absolute thresholds.

### Features

- **Real-time drive monitoring** - Output frequency, current, voltage, power, motor speed, and torque
- **Remote start/stop control** - Safely control the drive from anywhere with proper state sequencing
- **Speed setpoint adjustment** - Change drive speed reference remotely within configured limits
- **Comprehensive diagnostics** - DC bus voltage, drive temperature, run hours, and energy consumption tracking
- **Configurable alarms** - Set thresholds for high current, high temperature, and DC bus voltage with automatic alerts
- **Fault management** - View active fault codes with descriptions and remote fault reset capability
- **Emergency stop** - Immediate drive shutdown for safety-critical situations
- **Data logging** - Optional logging of all drive data to a channel for historical analysis
- **State machine** - Safe operation sequencing (disconnected, connected, ready, starting, running, stopping, fault, emergency)

<br/>

## Getting Started

### Prerequisites

1. **ABB ACQ580 VFD** with Modbus TCP communication enabled
2. **Network connectivity** between the Doovit device and the drive (or Modbus gateway)
3. **Modbus configuration** on the drive:
   - Drive must be configured for Modbus TCP communication
   - Remote control must be enabled in the drive parameters
   - Note the drive's IP address, port (typically 502), and Modbus unit ID

### Installation

1. Add the ACQ580 app to your Doovit device through the Doover platform
2. Configure the Modbus connection parameters to match your drive setup
3. Enter the connected load information (motor nameplate data)
4. Set appropriate alarm thresholds for your application
5. Enable or disable remote control as needed

### Quick Start

1. **Configure connection**: Set the drive's IP address and Modbus parameters
2. **Verify connectivity**: Check the "Connected" status in the Connection section
3. **Review status**: Confirm the drive shows "Ready" state before attempting control
4. **Test monitoring**: Verify output measurements match local drive display
5. **Enable control**: If remote control is enabled, use Start/Stop buttons to control the drive

<br/>

## Configuration

### General Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Display Name** | Name to display for this drive instance | ACQ580 Drive |
| **Control Enabled** | Allow remote start/stop and speed control commands | true |

### Modbus Connection

| Setting | Description | Default |
|---------|-------------|---------|
| **Host** | IP address or hostname of the Modbus gateway/drive | 192.168.1.100 |
| **Port** | Modbus TCP port | 502 |
| **Unit ID** | Modbus unit/slave ID (1-247) | 1 |
| **Timeout** | Communication timeout in seconds | 3.0 |

### Connected Load

| Setting | Description | Default |
|---------|-------------|---------|
| **Load Type** | Type of load connected (e.g., Pump, Fan, Conveyor, Compressor) | Pump |
| **Load Name** | Name/identifier for the connected load | Main Pump |
| **Rated Power kW** | Rated power of the connected motor in kW | 11.0 |
| **Rated Speed RPM** | Rated speed of the connected motor in RPM | 1450.0 |
| **Rated Voltage V** | Rated voltage of the connected motor in Volts | 400.0 |
| **Rated Current A** | Rated current of the connected motor in Amps | 22.0 |

### Operating Parameters

| Setting | Description | Default |
|---------|-------------|---------|
| **Max Frequency Hz** | Maximum output frequency limit in Hz | 50.0 |
| **Min Frequency Hz** | Minimum output frequency limit in Hz | 0.0 |
| **Accel Time s** | Acceleration time in seconds (0 to max freq) | 10.0 |
| **Decel Time s** | Deceleration time in seconds (max freq to 0) | 10.0 |

### Monitoring

| Setting | Description | Default |
|---------|-------------|---------|
| **Poll Interval s** | How often to poll drive status (seconds) | 2.0 |
| **Log Data to Channel** | Enable logging of drive data to a channel | true |

### Alarm Thresholds

| Setting | Description | Default |
|---------|-------------|---------|
| **High Current %** | Alarm when current exceeds this % of rated | 90.0 |
| **High Temperature C** | Alarm when drive temperature exceeds this (Celsius) | 70.0 |
| **Low DC Bus V** | Alarm when DC bus voltage drops below this | 500.0 |
| **High DC Bus V** | Alarm when DC bus voltage exceeds this | 750.0 |

### Example Configuration

```json
{
  "display_name": "Pump House VFD #1",
  "modbus_connection": {
    "host": "192.168.10.50",
    "port": 502,
    "unit_id": 1,
    "timeout": 3.0
  },
  "connected_load": {
    "load_type": "Pump",
    "load_name": "Raw Water Pump #1",
    "rated_power_kw": 15.0,
    "rated_speed_rpm": 1470,
    "rated_voltage_v": 400,
    "rated_current_a": 28.5
  },
  "operating_parameters": {
    "max_frequency_hz": 50.0,
    "min_frequency_hz": 15.0,
    "accel_time_s": 15.0,
    "decel_time_s": 20.0
  },
  "monitoring": {
    "poll_interval_s": 2.0,
    "log_data_to_channel": true
  },
  "alarm_thresholds": {
    "high_current_%": 85.0,
    "high_temperature_c": 65.0,
    "low_dc_bus_v": 520.0,
    "high_dc_bus_v": 720.0
  },
  "control_enabled": true
}
```

<br/>

## UI Elements

This application provides a comprehensive user interface organized into logical sections.

### Drive Status (Variables)

| Element | Description |
|---------|-------------|
| **Running** | Boolean indicator showing if the drive is running |
| **Ready** | Boolean indicator showing if the drive is ready to run |
| **Fault Active** | Boolean indicator showing if a fault condition exists |
| **Warning Active** | Boolean indicator showing if a warning condition exists |
| **Drive State** | Text showing current state (READY, RUNNING, ACCELERATING, FAULT, NOT READY) |
| **Fault Code** | Text showing active fault description if a fault exists |

### Output Measurements (Variables)

| Element | Description |
|---------|-------------|
| **Output Frequency** | Current output frequency in Hz (color-coded ranges) |
| **Output Current** | Current output current in Amps (color-coded ranges) |
| **Output Voltage** | Current output voltage in Volts |
| **Output Power** | Current output power in kW |
| **Motor Speed** | Current motor speed in RPM |
| **Motor Torque** | Current motor torque as percentage |

### Power Section (Variables)

| Element | Description |
|---------|-------------|
| **DC Bus Voltage** | Internal DC bus voltage in Volts (color-coded ranges) |
| **Drive Temperature** | Drive heatsink temperature in Celsius (color-coded ranges) |
| **Run Hours** | Total accumulated run hours |
| **Energy Consumed** | Total energy consumption in kWh |

### Control (Parameters and Actions)

| Element | Type | Description |
|---------|------|-------------|
| **Speed Setpoint** | Parameter | Numeric input to set target frequency in Hz |
| **Active Setpoint** | Variable | Display of the current active speed reference |
| **Control Mode** | State Command | Select between Remote and Local Panel control |
| **Start Drive** | Action | Green button to start the drive |
| **Stop Drive** | Action | Red button to stop the drive (normal stop) |
| **Reset Fault** | Action | Yellow button to reset a fault condition (requires confirmation) |
| **Emergency Stop** | Action | Red button for emergency stop (requires confirmation) |

### Alarms (Warning Indicators)

| Element | Description |
|---------|-------------|
| **High Current** | Appears when output current exceeds configured threshold |
| **High Temperature** | Appears when drive temperature exceeds configured threshold |
| **DC Bus Voltage** | Appears when DC bus voltage is outside configured range |
| **Communication Lost** | Appears when Modbus communication is lost |

### Connection (Variables)

| Element | Description |
|---------|-------------|
| **Connected** | Boolean indicator showing Modbus connection status |
| **Last Update** | Timestamp of last successful data poll |
| **Comm Errors** | Counter of communication errors since startup |

<br/>

## Tags

This application exposes the following tags for integration with other apps:

| Tag | Description |
|-----|-------------|
| **running** | Boolean indicating if the drive is currently running |
| **ready** | Boolean indicating if the drive is ready to run |
| **fault** | Boolean indicating if a fault condition is active |
| **output_frequency** | Current output frequency in Hz |
| **output_current** | Current output current in Amps |
| **output_power** | Current output power in kW |
| **motor_speed** | Current motor speed in RPM |
| **state** | Current state machine state (disconnected, connected, ready, running, fault, etc.) |

<br/>

## How It Works

1. **Initialization**: On startup, the application establishes a Modbus TCP connection to the ACQ580 drive using the configured host, port, and unit ID.

2. **Continuous Polling**: The main loop runs at the configured poll interval (default 2 seconds), reading all status registers and measurements from the drive via Modbus.

3. **State Machine**: A state machine tracks the drive's operational state (disconnected, connected, ready, starting, running, stopping, fault, emergency) to ensure safe operation sequencing and prevent invalid commands.

4. **UI Updates**: All readings are translated to user-friendly UI elements with appropriate units, color-coded ranges, and status indicators.

5. **Alarm Monitoring**: Each poll cycle checks alarm conditions against configured thresholds. When an alarm transitions from inactive to active, an alert notification is sent.

6. **Data Logging**: If enabled, drive data is logged to a channel in JSON format for historical analysis and integration with other systems.

7. **Control Commands**: When users press control buttons (Start, Stop, Emergency Stop, Fault Reset) or change the speed setpoint, commands are sent to the drive via Modbus control word and reference registers.

8. **Tag Updates**: Key drive parameters are published as tags for other applications to consume (running, ready, fault, output_frequency, output_current, output_power, motor_speed, state).

<br/>

## Integrations

This application works with:

- **ABB ACQ580 VFDs** - Primary target device for water and wastewater applications
- **Other ABB drives** - May work with other ABB drives using similar Modbus register mapping (ACS580, ACS880, etc.)
- **Modbus TCP gateways** - Can communicate through gateways for serial-to-TCP conversion
- **Doover channels** - Logs data to channels for integration with dashboards and other apps
- **Doover tags** - Publishes state as tags for use by other processors or automations

<br/>

## Need Help?

- Email: support@doover.com
- [Doover Documentation](https://docs.doover.com)
- [App Developer Documentation](https://github.com/getdoover/acq580/blob/main/DEVELOPMENT.md)

<br/>

## Version History

### v0.1.0 (Current)
- Initial release
- Full drive monitoring (frequency, current, voltage, power, speed, torque)
- Power section monitoring (DC bus voltage, temperature, run hours, energy)
- Remote start/stop/emergency stop control
- Speed setpoint adjustment with configurable limits
- Fault code display and remote fault reset
- Configurable alarm thresholds with notifications
- State machine for safe operation sequencing
- Data logging to channels
- Tag publishing for integration with other apps

<br/>

## License

This app is licensed under the [Apache License 2.0](https://github.com/getdoover/acq580/blob/main/LICENSE).
