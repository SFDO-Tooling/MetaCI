from django import dispatch

# Sent whenever a build completes
build_complete = dispatch.Signal(providing_args=["build","status"])
