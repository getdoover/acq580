"""State machine for ACQ580 VFD application.

Manages the drive control states and transitions, ensuring safe operation
and proper sequencing of commands.
"""

import logging
from typing import TYPE_CHECKING

from pydoover.state import StateMachine

if TYPE_CHECKING:
    from .application import Acq580Application

log = logging.getLogger(__name__)


class Acq580State:
    """State machine for ACQ580 drive control.

    States:
    - disconnected: No communication with drive
    - connected: Communication established, drive not ready
    - ready: Drive ready to run
    - starting: Start command sent, waiting for confirmation
    - running: Drive running
    - stopping: Stop command sent, waiting for confirmation
    - fault: Drive in fault state
    - emergency: Emergency stop active

    The state machine handles:
    - Connection/disconnection events
    - Start/stop sequencing
    - Fault detection and reset
    - Emergency stop handling
    """

    state: str

    states = [
        {"name": "disconnected", "timeout": 10, "on_timeout": "attempt_reconnect"},
        {"name": "connected"},
        {"name": "ready"},
        {"name": "starting", "timeout": 10, "on_timeout": "start_timeout"},
        {"name": "running"},
        {"name": "stopping", "timeout": 10, "on_timeout": "stop_timeout"},
        {"name": "fault"},
        {"name": "emergency"},
    ]

    transitions = [
        # Connection transitions
        {"trigger": "connect", "source": "disconnected", "dest": "connected"},
        {"trigger": "disconnect", "source": "*", "dest": "disconnected"},
        {"trigger": "attempt_reconnect", "source": "disconnected", "dest": "disconnected"},

        # Ready transitions
        {"trigger": "drive_ready", "source": "connected", "dest": "ready"},
        {"trigger": "drive_ready", "source": "stopping", "dest": "ready"},
        {"trigger": "drive_not_ready", "source": "ready", "dest": "connected"},

        # Start/Stop transitions
        {"trigger": "start_command", "source": "ready", "dest": "starting"},
        {"trigger": "started", "source": "starting", "dest": "running"},
        {"trigger": "stop_command", "source": "running", "dest": "stopping"},
        {"trigger": "stop_command", "source": "starting", "dest": "stopping"},
        {"trigger": "stopped", "source": "stopping", "dest": "ready"},
        {"trigger": "start_timeout", "source": "starting", "dest": "fault"},
        {"trigger": "stop_timeout", "source": "stopping", "dest": "fault"},

        # Fault transitions
        {"trigger": "fault_detected", "source": "*", "dest": "fault"},
        {"trigger": "fault_reset", "source": "fault", "dest": "connected"},

        # Emergency stop transitions
        {"trigger": "emergency_stop", "source": "*", "dest": "emergency"},
        {"trigger": "emergency_reset", "source": "emergency", "dest": "connected"},

        # Running state - can detect ready from running if drive stops externally
        {"trigger": "drive_ready", "source": "running", "dest": "ready"},
    ]

    def __init__(self, app: "Acq580Application" = None):
        """Initialize the state machine.

        Args:
            app: Reference to the application for callbacks
        """
        self.app = app
        self.state_machine = StateMachine(
            states=self.states,
            transitions=self.transitions,
            model=self,
            initial="disconnected",
            queued=True,
        )
        self._start_requested = False
        self._stop_requested = False
        self._fault_reset_requested = False
        self._emergency_requested = False

    # =========================================================================
    # State Evaluation
    # =========================================================================

    async def evaluate_state(self, drive_status):
        """Evaluate current drive status and trigger appropriate transitions.

        Args:
            drive_status: DriveStatus object from Modbus client
        """
        if drive_status is None:
            # Lost communication
            if self.state != "disconnected":
                await self.disconnect()
            return

        # Communication restored
        if self.state == "disconnected":
            await self.connect()
            return

        # Check for faults
        if drive_status.fault and self.state != "fault":
            log.warning(f"Drive fault detected: {drive_status.fault_code}")
            await self.fault_detected()
            return

        # Handle emergency stop state
        if self._emergency_requested:
            self._emergency_requested = False
            await self.emergency_stop()
            return

        # Handle fault reset request
        if self._fault_reset_requested and self.state == "fault":
            self._fault_reset_requested = False
            await self.fault_reset()
            return

        # State-specific evaluation
        if self.state == "connected":
            if drive_status.ready:
                await self.drive_ready()

        elif self.state == "ready":
            if not drive_status.ready:
                await self.drive_not_ready()
            elif self._start_requested:
                self._start_requested = False
                await self.start_command()

        elif self.state == "starting":
            if drive_status.running:
                await self.started()
            elif self._stop_requested:
                self._stop_requested = False
                await self.stop_command()

        elif self.state == "running":
            if not drive_status.running:
                await self.drive_ready()
            elif self._stop_requested:
                self._stop_requested = False
                await self.stop_command()

        elif self.state == "stopping":
            if not drive_status.running and drive_status.ready:
                await self.stopped()

        elif self.state == "emergency":
            # Wait for explicit reset
            pass

    async def spin_state(self, drive_status, max_iterations: int = 5) -> str:
        """Spin the state machine until stable.

        Args:
            drive_status: DriveStatus object from Modbus client
            max_iterations: Maximum number of evaluation iterations

        Returns:
            The final stable state
        """
        for _ in range(max_iterations):
            old_state = self.state
            await self.evaluate_state(drive_status)
            if self.state == old_state:
                break
        return self.state

    # =========================================================================
    # Request Methods (called by application)
    # =========================================================================

    def request_start(self):
        """Request to start the drive."""
        if self.state == "ready":
            self._start_requested = True
            log.info("Start requested")

    def request_stop(self):
        """Request to stop the drive."""
        if self.state in ("running", "starting"):
            self._stop_requested = True
            log.info("Stop requested")

    def request_fault_reset(self):
        """Request to reset the drive fault."""
        if self.state == "fault":
            self._fault_reset_requested = True
            log.info("Fault reset requested")

    def request_emergency_stop(self):
        """Request emergency stop."""
        self._emergency_requested = True
        log.warning("Emergency stop requested!")

    # =========================================================================
    # State Callbacks
    # =========================================================================

    async def on_enter_disconnected(self):
        """Called when entering disconnected state."""
        log.warning("Drive communication lost")
        if self.app:
            self.app.ui.set_alarm("comms", True)

    async def on_exit_disconnected(self):
        """Called when exiting disconnected state."""
        if self.app:
            self.app.ui.set_alarm("comms", False)

    async def on_enter_connected(self):
        """Called when connection established."""
        log.info("Drive connected, waiting for ready")

    async def on_enter_ready(self):
        """Called when drive is ready."""
        log.info("Drive ready")

    async def on_enter_starting(self):
        """Called when start command sent."""
        log.info("Starting drive...")
        if self.app and self.app.modbus_client:
            await self.app.modbus_client.start()

    async def on_enter_running(self):
        """Called when drive confirmed running."""
        log.info("Drive running")

    async def on_enter_stopping(self):
        """Called when stop command sent."""
        log.info("Stopping drive...")
        if self.app and self.app.modbus_client:
            await self.app.modbus_client.stop()

    async def on_enter_fault(self):
        """Called when fault detected."""
        log.error("Drive in fault state!")
        if self.app:
            await self.app.ui.alerts.send_alert(
                f"Drive fault detected! Check fault code."
            )

    async def on_enter_emergency(self):
        """Called when emergency stop activated."""
        log.critical("Emergency stop active!")
        if self.app and self.app.modbus_client:
            await self.app.modbus_client.emergency_stop()
        if self.app:
            await self.app.ui.alerts.send_alert(
                "Emergency stop activated!"
            )

    async def on_exit_emergency(self):
        """Called when leaving emergency state."""
        log.info("Emergency stop reset")

    # Type hints for dynamically created trigger methods
    async def connect(self): ...
    async def disconnect(self): ...
    async def attempt_reconnect(self): ...
    async def drive_ready(self): ...
    async def drive_not_ready(self): ...
    async def start_command(self): ...
    async def started(self): ...
    async def stop_command(self): ...
    async def stopped(self): ...
    async def start_timeout(self): ...
    async def stop_timeout(self): ...
    async def fault_detected(self): ...
    async def fault_reset(self): ...
    async def emergency_stop(self): ...
    async def emergency_reset(self): ...
