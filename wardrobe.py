#!/usr/bin/env python

import atexit
import errno
import os
import sys
import tempfile

class Locker:
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
		if not self.lock():
			sys.exit('Could not acquire lock.')
	def unlock(self):
		if not self.locked:
			raise StateError('not locked, cannot unlock')
		os.rmdir(self.path)
		self.locked = False
	def unlockIfLocked(self):
		if self.locked:
			self.unlock()
