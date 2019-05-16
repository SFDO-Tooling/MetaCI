from django import db
import django_rq

from metaci.plan.models import PlanSchedule


def reset_database_connection():
    db.connection.close()


def run_scheduled(schedule):
    reset_database_connection()

    schedules = PlanSchedule.objects.filter(schedule=schedule)

    log = []
    log.append("Found {} {} schedules to run".format(schedules.count(), schedule))

    for sched in schedules:
        try:
            build = sched.run()
            log.append(
                "Created build #{} from Plan {} on branch {}".format(
                    build.id, sched.plan, sched.branch
                )
            )

        except Exception as e:
            log.append("Schedule {} failed with error:\n{}".format(sched, str(e)))

    return "\n".join(log)


@django_rq.job("short")
def run_scheduled_daily():
    return run_scheduled("daily")


@django_rq.job("short")
def run_scheduled_hourly():
    return run_scheduled("hourly")
