"""
Worker Thread Framework
======================

A flexible framework for managing worker threads in PyQt applications.
"""

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer
import threading
import logging
import uuid
import traceback
from typing import TypedDict


class Worker(QObject):
    """Base worker class that runs on its own thread

    Signals:
        started: Emitted when the worker starts its work
        finished: Emitted when the worker completes or is stopped
        error: Emitted when an error occurs, with error message
    """

    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, logger: logging.Logger, name=None):
        """Initialize a new worker

        Args:
            name: Optional name for the worker (defaults to auto-generated)
        """
        super().__init__()
        self._name = name or f"Worker-{str(uuid.uuid4())[:8]}"
        self._stop_requested = False
        self._logger = logger

    @property
    def name(self):
        """Get the worker's name"""
        return self._name

    @property
    def is_stopping(self):
        """Check if stop has been requested"""
        return self._stop_requested

    def _run(self):
        """Internal method that should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

    def _on_stop_requested(self):
        """Override this method to handle any custom cleanup logic"""
        pass

    def start_work(self):
        """Main work method that gets called when thread starts.

        This method is automatically called when the thread starts.
        Override this method in subclasses to implement worker logic.
        """
        try:
            self._logger.info(
                f"[{threading.current_thread().name}] {self._name}: starting work on thread: {self._thread_name()}"
            )
            self.started.emit()
            self._run()
        except Exception as e:
            self._logger.debug(traceback.format_exc())
            self.error.emit(str(e))

    def stop_work(self):
        """Request the worker to stop.

        This sets the stop flag which should be checked by the worker's
        _run method to terminate cleanly.
        """
        self._stop_requested = True
        self._on_stop_requested()

    def _thread_name(self):
        """Get the current thread name"""
        return threading.current_thread().name


class WorkerRecord(TypedDict):
    worker: Worker
    thread: QThread


class ThreadController:
    """Manages worker threads with proper lifecycle management"""

    def __init__(self, logger: logging.Logger):
        """Initialize the thread controller"""
        self.workers: dict[str, WorkerRecord] = {}
        self._logger = logger
        self._thread_name = threading.current_thread().name

    def add_worker(self, worker, auto_start=False):
        """Add a worker to be managed

        Args:
            worker: The Worker instance to manage
            auto_start: Whether to start the worker immediately

        Returns:
            worker_name: The name of the added worker

        Raises:
            ValueError: If a worker with the same name already exists
        """
        if worker.name in self.workers:
            return worker.name

        # Create thread and set name
        thread = QThread()
        thread.setObjectName(f"thread-{worker.name}")

        worker.error.connect(lambda e: self._logger.error(f"[[{self._thread_name}]] {worker.name} error: {e}"))
        worker.finished.connect(lambda: self.stop_worker(worker.name))

        worker.moveToThread(thread)

        # Store worker and thread
        self.workers[worker.name] = WorkerRecord(worker=worker, thread=thread)

        self._logger.info(f"[{self._thread_name}] added worker: {worker.name}")

        if auto_start:
            self.start_worker(worker.name)

        return worker.name

    def start_worker(self, worker_name):
        """Start a specific worker thread

        Args:
            worker_name: Name of the worker to start

        Returns:
            bool: True if started successfully

        Raises:
            ValueError: If worker is not found
        """
        if worker_name not in self.workers:
            raise ValueError(f"No worker named '{worker_name}' found")

        worker_data = self.workers[worker_name]
        worker_data["worker"]._stop_requested = False

        # Connect signals and slots
        worker_data["thread"].started.connect(lambda: QTimer.singleShot(0, worker_data["worker"].start_work))

        worker_data["thread"].start()
        self._logger.info(f"[{self._thread_name}] started worker: {worker_name}")
        return True

    def stop_worker(self, worker_name):
        """Stop a specific worker thread

        Args:
            worker_name: Name of the worker to stop

        Raises:
            ValueError: If worker is not found
        """
        if worker_name not in self.workers:
            return None

        worker_data = self.workers[worker_name]
        worker_data["worker"].stop_work()
        worker_data["worker"].error.disconnect()
        worker_data["thread"].started.disconnect()

        worker_data["thread"].quit()
        success = worker_data["thread"].wait(3000)

        if success:
            self._logger.info(f"[{self._thread_name}] stopped worker: {worker_name}")
            self.workers.pop(worker_name, None)
        else:
            self._logger.warning(f"[{self._thread_name}] worker did not stop cleanly: {worker_name}")

    def start_all(self):
        """Start all worker threads"""
        self._logger.info(f"[{self._thread_name}] starting all workers")
        for worker_name in self.workers:
            self.start_worker(worker_name)

    def stop_all(self):
        """Stop all worker threads"""
        self._logger.info(f"[{self._thread_name}] stopping all workers")
        for worker_name in list(self.workers.keys()):
            self.stop_worker(worker_name)

    def cleanup(self):
        """Force cleanup of threads that haven't stopped properly"""
        self._logger.info(f"[{self._thread_name}] performing final cleanup")
        for worker_name, worker_data in list(self.workers.items()):
            if worker_data["thread"].isRunning():
                self._logger.warning(f"[{self._thread_name}] forcing thread to terminate: {worker_name}")
                worker_data["thread"].terminate()
                worker_data["thread"].wait()
            self.workers.pop(worker_name, None)

    def get_worker_by_name(self, worker_name) -> Worker | None:
        """Get a worker by name"""
        worker_data = self.workers.get(worker_name, None)
        if not worker_data:
            raise ValueError(f"No worker named '{worker_name}' found")
        return worker_data.get("worker", None)
