from PyQt5.QtCore import QTimer, QMetaObject, pyqtSignal, QThread, Q_ARG
from worker_framework import Worker
import logging


class TimerWorker(Worker):
    """Worker that runs a timer on its own thread

    Signals:
        timer_tick: Emitted on each timer tick with tick count
    """

    timer_tick = pyqtSignal(int)

    def __init__(self, logger: logging.Logger, interval=1000, name=None):
        """Initialize a timer worker

        Args:
            interval: Timer interval in milliseconds
            name: Optional worker name
        """
        super().__init__(logger, name=name)
        self.interval = interval
        self.timer = QTimer()
        self.timer.moveToThread(None)  # Initially not in any thread
        self.counter = 0

    def _run(self):
        """Set up and start the timer"""
        # Ensure timer is in the current thread
        self.timer.moveToThread(QThread.currentThread())
        # Connect timeout in the current thread's context
        self.timer.timeout.connect(self._on_timeout)
        # Start timer safely using QMetaObject
        QMetaObject.invokeMethod(self.timer, "start", Q_ARG(int, self.interval))

    def _on_stop_requested(self):
        """Handle stop request by stopping the timer"""
        # Schedule deletion of timer in its own thread
        if self.timer is not None:
            # Disconnect the timer first to prevent further timeouts
            self.timer.timeout.disconnect(self._on_timeout)
            # Schedule the timer to be deleted in its own thread
            self.timer.deleteLater()
            self.timer = None

    def _on_timeout(self):
        """Handle timer timeout events"""
        self.timer_tick.emit(self.counter)
