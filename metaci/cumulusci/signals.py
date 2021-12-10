from django import dispatch


# Sent whenever an org is claimed from an org pool
# provided signal args: 'org_pool'
org_claimed = dispatch.Signal()
