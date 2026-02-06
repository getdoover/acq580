# Build Plan

## App Summary
- Name: acq580
- Type: docker
- Description: Interface with ABB ACQ580 Variable Frequency Drive (VFD) for pump control, allowing configuration of connected loads and providing full monitoring and remote control capabilities via Modbus TCP.

## External Integration
- Service: ABB ACQ580 VFD via Modbus TCP
- Documentation:
  - [ABB ACQ580 Firmware Manual](https://gibbonsgroup.co.uk/wp-content/uploads/2018/09/ACQ580-01-Firmware-Manual.pdf)
  - [ABB Modbus RTU for Drives](https://new.abb.com/drives/connectivity/fieldbus-connectivity/modbus-rtu)
  - [Modbus Register Mapping Technical Note](https://library.e.abb.com/public/bcf106976d444604a93646d66c32bbca/Technical_Note_062_Modbus_registers_for_550_to_580_series_conversion.pdf)
- Authentication: N/A (Modbus uses unit ID addressing)

## Data Flow
- Inputs:
  - Modbus TCP holding registers from ACQ580 drive
  - Status word (running, ready, fault, warning states)
  - Actual values (frequency, current, voltage, power, speed, torque)
  - DC bus voltage and drive temperature
  - Fault and warning codes
  - Run hours and energy consumption

- Processing:
  - Parse status word bits for drive state
  - Convert register values to engineering units (scaling)
  - State machine to sequence start/stop operations safely
  - Alarm condition monitoring against configurable thresholds
  - Alert deduplication (only notify on rising edge)

- Outputs:
  - Control word writes (start, stop, fault reset, emergency stop)
  - Speed reference setpoint
  - UI updates (all variables and indicators)
  - Tags for inter-app communication
  - Channel data logging (JSON payloads)
  - Alert notifications

## Configuration Schema
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| display_name | string | no | "ACQ580 Drive" | Display name for this drive instance |
| modbus_connection.host | string | yes | "192.168.1.100" | IP address or hostname of Modbus gateway/drive |
| modbus_connection.port | integer | yes | 502 | Modbus TCP port |
| modbus_connection.unit_id | integer | yes | 1 | Modbus unit/slave ID (1-247) |
| modbus_connection.timeout | number | yes | 3.0 | Communication timeout in seconds |
| connected_load.load_type | string | yes | "Pump" | Type of load (Pump, Fan, Conveyor, Compressor) |
| connected_load.load_name | string | yes | "Main Pump" | Name/identifier for the connected load |
| connected_load.rated_power_kw | number | yes | 11.0 | Rated motor power in kW |
| connected_load.rated_speed_rpm | number | yes | 1450.0 | Rated motor speed in RPM |
| connected_load.rated_voltage_v | number | yes | 400.0 | Rated motor voltage in Volts |
| connected_load.rated_current_a | number | yes | 22.0 | Rated motor current in Amps |
| operating_parameters.max_frequency_hz | number | yes | 50.0 | Maximum output frequency limit |
| operating_parameters.min_frequency_hz | number | yes | 0.0 | Minimum output frequency limit |
| operating_parameters.accel_time_s | number | yes | 10.0 | Acceleration time (0 to max freq) |
| operating_parameters.decel_time_s | number | yes | 10.0 | Deceleration time (max freq to 0) |
| monitoring.poll_interval_s | number | yes | 2.0 | Status poll interval in seconds |
| monitoring.log_data_to_channel | boolean | yes | true | Enable channel data logging |
| alarm_thresholds.high_current_pct | number | yes | 90.0 | High current alarm (% of rated) |
| alarm_thresholds.high_temperature_c | number | yes | 70.0 | High temperature alarm (Celsius) |
| alarm_thresholds.low_dc_bus_v | number | yes | 500.0 | Low DC bus voltage alarm |
| alarm_thresholds.high_dc_bus_v | number | yes | 750.0 | High DC bus voltage alarm |
| control_enabled | boolean | yes | true | Allow remote start/stop and speed control |

## UI Elements

### Variables (Display)
| Name | Type | Description |
|------|------|-------------|
| running | BooleanVariable | Drive running state |
| ready | BooleanVariable | Drive ready state |
| fault | BooleanVariable | Fault active indicator |
| warning | BooleanVariable | Warning active indicator |
| drive_state | TextVariable | Human-readable drive state |
| fault_code | TextVariable | Active fault description |
| output_frequency | NumericVariable | Output frequency (Hz) with range coloring |
| output_current | NumericVariable | Output current (A) with range coloring |
| output_voltage | NumericVariable | Output voltage (V) |
| output_power | NumericVariable | Output power (kW) |
| motor_speed | NumericVariable | Motor speed (RPM) |
| motor_torque | NumericVariable | Motor torque (%) |
| dc_bus_voltage | NumericVariable | DC bus voltage (V) with range coloring |
| drive_temperature | NumericVariable | Drive temperature (C) with range coloring |
| run_hours | NumericVariable | Accumulated run hours |
| energy_kwh | NumericVariable | Energy consumed (kWh) |
| speed_setpoint_display | NumericVariable | Active speed setpoint (Hz) |
| connected | BooleanVariable | Communication connected state |
| last_update | DateTimeVariable | Timestamp of last successful update |
| comms_errors | NumericVariable | Communication error count |

### Parameters (User Input)
| Name | Type | Default | Description |
|------|------|---------|-------------|
| speed_setpoint | NumericParameter | - | Speed setpoint entry (Hz) |
| control_mode | StateCommand | "remote" | Control mode selection (Remote/Local) |

### Actions (Commands)
| Name | Description |
|------|-------------|
| start_drive | Start the drive (green, position 1) |
| stop_drive | Stop the drive (red, position 2) |
| fault_reset | Reset fault (yellow, requires confirm, position 3) |
| emergency_stop | Emergency stop (red, requires confirm, position 4) |

### Warning Indicators
| Name | Description |
|------|-------------|
| high_current_alarm | High current warning (hidden by default) |
| high_temp_alarm | High temperature warning (hidden by default) |
| dc_bus_alarm | DC bus voltage warning (hidden by default) |
| comms_alarm | Communication lost warning (hidden by default) |

## Documentation Chunks

### Required Chunks
- `config-schema.md` - Configuration types and patterns
- `docker-application.md` - Application class structure
- `docker-project.md` - Entry point and Dockerfile

### Recommended Chunks
- `docker-ui.md` - UI component patterns (has_ui=true)
- `docker-advanced.md` - State machine and Modbus interface patterns
- `tags-channels.md` - Tag and channel publishing patterns

### Discovery Keywords
- modbus, vfd, drive, motor, frequency, current, voltage, power, torque
- state machine, transition, timeout, fault, warning, alarm, alert
- control word, status word, register, holding register
- pump, fan, speed, setpoint, reference

## Implementation Notes

### Modbus Register Mapping
The ACQ580 uses ABB's standard Modbus register mapping:
- Control Word: Register 0 (write)
- Status Word: Register 1 (read)
- Speed Reference: Register 2 (0.01 Hz resolution)
- Actual Values: Registers 3-12 (frequency, current, voltage, power, speed, torque, DC bus, temp, run hours, energy)
- Fault/Warning Codes: Registers 50-51

### State Machine States
- `disconnected` - No communication (10s timeout for reconnect)
- `connected` - Communication established, drive not ready
- `ready` - Drive ready to run
- `starting` - Start command sent (10s timeout)
- `running` - Drive confirmed running
- `stopping` - Stop command sent (10s timeout)
- `fault` - Drive in fault state
- `emergency` - Emergency stop active

### External Packages Needed
- `pymodbus` - Async Modbus TCP client (already in dependencies)

### Main Loop Interval
- Configurable via `monitoring.poll_interval_s`, default 2 seconds
- Appropriate for monitoring drive status without excessive network traffic

### Key Patterns Used
- State machine with timeouts for safe operation sequencing
- Alert deduplication to prevent notification spam
- Range coloring on numeric displays for at-a-glance status
- Configurable alarm thresholds
- Channel logging for historical data
- Tags for inter-app communication
- Submodule grouping for organized UI

### Current Implementation Status
The app has a complete implementation including:
- [x] Configuration schema (app_config.py)
- [x] Modbus client with register definitions (modbus_client.py)
- [x] State machine for safe operation (app_state.py)
- [x] Full UI with all components (app_ui.py)
- [x] Application class with callbacks (application.py)
- [x] doover_config.json with schema
- [ ] Simulator for local testing (needs implementation)
- [ ] Unit tests (basic structure exists)

### Remaining Work
1. Implement simulator application to test without real hardware
2. Add unit tests for state machine transitions
3. Verify Modbus register addresses against actual ACQ580 documentation
4. Test alarm threshold logic with edge cases
5. Consider adding PID control support (ACQ580 has built-in PID)
