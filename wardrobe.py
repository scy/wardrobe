#!/usr/bin/env python

import atexit
import errno
import os
import sys
import tempfile

class Locker:
	class AcquireError(StandardError):
		"""The requested lock could not be acquired."""
		pass
	path = None
	locked = False
	def __init__(self, ensurenow = False, directory = 'wardrobe.lock.d'):
		if not isinstance(directory, str):
			raise TypeError('directory has to be a string')
		self.path = os.path.join(tempfile.gettempdir(), directory)
		if ensurenow:
			self.ensure()
	def __del__(self):
		self.unlockIfLocked()
	def lock(self):
		# Don't lock again if we already own a lock.
		if self.locked:
			return (True)
		try:
			os.mkdir(self.path)
		except OSError, e:
			if e.errno == errno.EEXIST:
				return (False)
			raise e
		self.locked = True
		atexit.register(self.unlockIfLocked)
		return (True)
	def ensure(self):
		"""Try to lock and raise an `AcquireError` if this fails."""
		if not self.lock():
			raise self.AcquireError(
				"could not acquire lock '%s'" % self.path
			)
	def unlock(self):
		if not self.locked:
			raise StateError('not locked, cannot unlock')
		os.rmdir(self.path)
		self.locked = False
	def unlockIfLocked(self):
		if self.locked:
			self.unlock()
