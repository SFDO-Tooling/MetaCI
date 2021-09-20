from datetime import datetime
from datetime import timedelta

from django import db
from django.utils import timezone
from django_rq import job

from metaci.release.models import ReleaseCohort, Release


@job("short")
def merge_freeze_job() -> str:
    """Determine if any merge freeze windows have started/stopped.
    If a window on a release cohort has started then we need to apply 
    a failing merge freeze check to open pull requests in the repo.
    If a window on a release cohort has ended, then we need to apply a
    passing merge freeze check to all open pull requests.      


    repo a - in scope for both of the following cohorts
    c1 - ends today
    c2 - starts today
    """
    apply_freeze = ()
    lift_freeze = ()
    cohorts = ReleaseCohort.objects.all()

    for cohort in cohorts:
        # if merge freeze start time is greater than
        # 7-8 min ago and less than now.
        if cohort.merge_freeze_start < datetime.now().isoformat() \
        and cohort.merge_freeze_start > (datetime.now() - timedelta(min=-8)).isoformat():  
            apply_freeze.append(cohort.releases.repository.name)    
        
        # if merge freeze end time is greater than
        # 7-8 min ago and less than now.
            # check if they're in scope for some other cohort that is still active
            # if not, add them to the list of repos we will lift merge freeze on
        if cohort.merge_freeze_end < datetime.now().isoformat() \
        and cohort.merge_freeze_end > (datetime.now() - timedelta(min=-8)).isoformat():  
            lift_freeze.append(cohort.release.repository.name)
            
            
    if apply_freeze:
        for repository in apply_freeze: 
            # TODO
            set_merge_freeze_status(repository.name, freeze=True)

    if lift_freeze: 
        for repository in lift_freeze: 
            # TODO
            set_merge_freeze_status(cohort.repository.name, freeze=False)


