from model_utils.choices import Choices

SUPERTYPES = Choices(
    ('ci', 'CI Test Org'),
    ('registered', 'Registered Org'),
)
ORGTYPES = Choices(
    ('scratch', 'Scratch Org Definition'),
    ('packaging', 'Packaging Org'),
    ('unmanaged', 'Persistent Test Org (Unmanaged)'),
    ('beta', 'Persistent Test Org (Beta Package)'),
    ('production', 'Persistent Test Org (Production Package)'),
    ('trial', 'Trial Source Org (Production Package'),
    ('admin', 'Administrative Org (no package)'),
)

PUSHSCHEDULES = Choices(
    ('QA', 'QA Orgs')
)

ORG_PERMISSIONS = Choices(
        ('manage_locks', 'manage locks'),
        ('run_builds', 'run builds'),
        ('login', 'login'),
)

ORG_ACTION_FLAGS = Choices('lock', 'unlock', 'run', 'login', 'other')
