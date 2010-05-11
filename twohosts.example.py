#!/usr/bin/env python

from wardrobe import *

# This will ensure only one wardrobe process runs simultaneously.
# "True" means "lock directly when creating the instance".
# Unlocking takes place automatically when the script ends.
l = Locker(True)

# A sane default filter for Unix systems.
unixfilter = FilterSet(Exclude('/proc/*'), Exclude('/sys/*'))

# A new backup run template.
unix = BackupRun()
# Ignore ACLs and EAs.
unix.acls = unix.eas = False
# Preserve numerical IDs.
unix.preservenumericalids = True
# Set verbosity to 5.
unix.verbosity = 5
# Set the filters to use to our instance from above.
unix.filters = unixfilter

# This generator creates sources and destinations for pulling complete hosts
# into a specified backup directory. "a.dotsunited.de" will be stored in
# "/var/backup/data/a.dotsunited.de".
generator = PullCompleteHost('/var/backup/data')

# Sequencially and unconditionally backup these hosts.
for host in ('a.dotsunited.de', 'b.dotsunited.de'):
	# Create a new backup run based on our template from above.
	r = BackupRun(unix)
	# Take source and destination from the generator.
	(r.source, r.destination) = generator.generate(host)
	# Run.
	r.run()
