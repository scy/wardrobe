#!/usr/bin/env python

import atexit
import errno
import os
import sys
import tempfile

class Locker(object):
	"""
	Filesystem-based atomic locking.
	
	Please note that this class is not designed to be thread-safe.
	"""

	class AcquireError(StandardError):
		"""The requested lock could not be acquired."""

	class StateError(StandardError):
		"""The operation is not valid in the current state."""

	_path = None
	"""The complete path to the locking directory."""

	_locked = False
	"""Whether this instance is currently holding a lock or not."""

	def __init__(self, locknow = False, directory = 'wardrobe.lock.d'):
		"""
		Initialize a new locker that will use the directory in the system's
		temp directory for locking.
		
		If locknow is set, the lock will be requested instantly; creating an
		instance will fail if it can not be acquired.
		"""
		if not isinstance(directory, str):
			raise TypeError('directory has to be a string')
		self._path = os.path.join(tempfile.gettempdir(), directory)
		if locknow:
			self.lock()

	def __del__(self):
		"""
		When this instance is unloaded, release possible locks.
		"""
		self.unlockIfLocked()

	def _lock(self):
		"""
		Acquire the lock, assuming that all state checks have already been made.
		"""
		# Try to acquire the lock.
		try:
			os.mkdir(self._path)
		except OSError, e:
			if e.errno == errno.EEXIST:
				# The directory (i.e. the lock) already exists.
				raise self.AcquireError(
					"could not acquire lock '%s'" % self._path
					)
			raise e
		# We acquired the lock successfully. Register an atexit.
		self._locked = True
		atexit.register(self.unlockIfLocked)
		return True

	def _unlock(self):
		"""
		Release the lock, assuming that all state checks have already been made.
		"""
		# Try to release the lock. OSErrors will propagate.
		# Warning: Without state checks, the directory will be removed even if
		# it was not created by this instance! (However, only empty directories
		# will be removed.)
		os.rmdir(self._path)
		self._locked = False
		return True

	def isLocked(self):
		"""
		Return whether this instance holds a lock or not.
		"""
		return self._locked

	def lock(self):
		"""
		Acquire the lock.
		
		If already locked, a StateError is raised. If the lock could not be
		acquired, an AcquireError is raised. Return True.
		"""
		if self._locked:
			raise self.StateError('already locked, cannot lock again')
		return self._lock()

	def lockIfUnlocked(self):
		"""
		Acquire the lock if this instance is not already holding one.
		
		If a lock is already held, return True. If not, one is acquired and True
		is returned. If acquiring fails, an AcquireError is raised.
		"""
		# Don't lock again if we already own a lock.
		if self._locked:
			return True
		return self._lock()

	def unlock(self):
		"""
		Release the lock.
		
		If not locked, a StateError is raised. If the lock can not be released,
		an error (most likely OSError) is raised. Return True.
		"""
		if not self._locked:
			raise self.StateError('not locked, cannot unlock')
		return self._unlock()

	def unlockIfLocked(self):
		"""
		Release the lock if this instance is holding one.
		
		If no lock is held, return True. Else, behave like unlock(), except that
		no StateError will be raised.
		"""
		if self._locked:
			self._unlock()
