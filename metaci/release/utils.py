# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import re

from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_datetime

from metaci.repository.utils import get_github_api

logger = logging.getLogger(__name__)

def update_release_from_github(release):
    if not release.git_tag:
        logger.info('Cannot update release, no git_tag specified')
        return
    repo = get_github_api(release.repo)
    ref = repo.ref('tags/{}'.format(release.git_tag))
    if not ref:
        logger.info(
            'Cannot update release, ref tags/{} not found in Github'.format(release.git_tag)
        )
        return
    url = repo._build_url('releases/tags/{}'.format(release.git_tag), base_url=repo._api)
    gh_release = repo._get(url).json()
    release.status = 'published'
    release.version_name = gh_release['name']
    release.version_number = gh_release['name']
    release.github_release = gh_release['html_url']
    release.release_creation_date = parse_datetime(gh_release['created_at'])
    release.created_from_commit = ref.object.sha
    sandbox_date = re.findall(
        r'^Sandbox orgs: (20[\d][\d]-[\d][\d]-[\d][\d])', gh_release['body']
    )
    if sandbox_date:
        release.sandbox_push_date = parse_date(sandbox_date[0], '%Y-%m-%d')

    prod_date = re.findall(
        r'^Production orgs: (20[\d][\d]-[\d][\d]-[\d][\d])', gh_release['body']
    )
    if prod_date:
        release.production_push_date = parse_date(prod_date[0], '%Y-%m-%d')

    package_version_id = re.findall(r'(04t[\w]{15,18})', gh_release['body'])
    if package_version_id:
        release.package_version_id = package_version_id[0]

    trialforce_id = re.findall(
        r'^(0TT[\w]{15,18})', gh_release['body']
    )
    if trialforce_id:
        release.trialforce_id = trialforce_id[0]
