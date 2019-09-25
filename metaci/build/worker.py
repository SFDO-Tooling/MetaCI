import errno
import os
import signal

from django.core.cache import cache
from rq.worker import signal_name
from rq.worker import StopRequested
from rq.worker import Worker

from metaci.build.autoscaling import STARTING_WORKERS_KEY


class RequeueingWorker(Worker):
    """An extension of the base rq worker which handles requeueing the job
    if SIGTERM or SIGINT causes the worker to close.  This currently uses
    the delay method on the target function so the function must support that
    """

    def _install_signal_handlers(self):
        """Installs signal handlers for handling SIGINT and SIGTERM
        gracefully.
        """

        def request_force_stop(signum, frame):
            """Terminates the application (cold shutdown)."""
            self.log.warning("Cold shut down.")

            # If shutdown is requested in the middle of a job,
            # requeue the job
            if self.get_current_job():
                job = self.get_current_job()
                job.func.delay(*job.args, **job.kwargs)

            # Take down the horse with the worker
            if self.horse_pid:
                msg = "Taking down horse %d with me." % self.horse_pid
                self.log.debug(msg)
                try:
                    os.kill(self.horse_pid, signal.SIGKILL)
                except OSError as e:
                    # ESRCH ("No such process") is fine with us
                    if e.errno != errno.ESRCH:
                        self.log.debug("Horse already down.")
                        raise
            raise SystemExit()

        def request_stop(signum, frame):
            """Stops the current worker loop but waits for child processes to
            end gracefully (warm shutdown).
            """
            self.log.debug("Got signal %s." % signal_name(signum))

            signal.signal(signal.SIGINT, request_force_stop)
            signal.signal(signal.SIGTERM, request_force_stop)

            msg = "Warm shut down requested."
            self.log.warning(msg)

            # If shutdown is requested in the middle of a job, wait until
            # finish before shutting down
            if self.get_current_job():
                self._stopped = True
                self.log.debug(
                    "Stopping after current horse is finished. "
                    "Press Ctrl+C again for a cold shutdown."
                )
            else:
                raise StopRequested()

        signal.signal(signal.SIGINT, request_stop)
        signal.signal(signal.SIGTERM, request_stop)
