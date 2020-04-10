from rq import requeue_job


class BuildError(Exception):
    pass


class RequeueJob(Exception):
    pass


def maybe_requeue_job(job, exc_type, exc_value, traceback):
    # If the job raised RequeueJob, requeue it.
    # (This is done here in an rq exception handler
    # because it can't be requeued until it is in the failed job registry.)
    if isinstance(exc_value, RequeueJob):
        requeue_job(job.id, None)
        return False
