import django_rq
from django import db

from metaci.plan.models import PlanSchedule


def reset_database_connection():
    db.connection.close()


def run_scheduled(schedule):
    reset_database_connection()

    schedules = PlanSchedule.objects.filter(schedule=schedule)

    log = []
    log.append(f"Found {schedules.count()} {schedule} schedules to run")

    for sched in schedules:
        try:
            build = sched.run()
            log.append(
                f"Created build #{build.id} from Plan {sched.plan} on branch {sched.branch}"
            )

        except Exception as e:
            log.append(f"Schedule {sched} failed with error:\n{str(e)}")

    return "\n".join(log)


@django_rq.job("short")
def run_scheduled_monthly():
    return run_scheduled("monthly")


@django_rq.job("short")
def run_scheduled_weekly():
    return run_scheduled("weekly")


@django_rq.job("short")
def run_scheduled_daily():
    return run_scheduled("daily")


@django_rq.job("short")
def run_scheduled_hourly():
    return run_scheduled("hourly")
