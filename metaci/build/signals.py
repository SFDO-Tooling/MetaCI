from django import dispatch

# Sent whenever a build completes
# provided signal args: 'build', 'status'
build_complete = dispatch.Signal()
