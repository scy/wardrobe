#!/usr/bin/env python

import atexit
import errno
import os
import sys
import tempfile



class SettingCombinationError(StandardError):
	"""You have tried to combine settings which are not combinable."""



class Locker(object):
	"""
	Filesystem-based atomic locking.
	
	Please note that this class is not designed to be thread-safe.
	"""

	class AcquireError(StandardError):
		"""The requested lock could not be acquired."""

	class StateError(StandardError):
		"""The operation is not valid in the current state."""

	def _getpath(self):
		"""
		The complete path to the locking directory.
		
		When setting this property to a relative path, it will be qualified by
		prepending the system's temp directory to it.
		"""
		return self._path

	def _setpath(self, value):
		if not isinstance(value, str):
			raise TypeError('path has to be a string')
		if os.path.isabs(value):
			self._path = value
		else:
			self._path = os.path.join(tempfile.gettempdir(), value)

	path = property(_getpath, _setpath)

	def _getlocked(self):
		"""
		Whether this instance is currently holding a lock or not. Read-only.
		"""
		return self._locked

	locked = property(_getlocked)

	def __init__(self, locknow = False, directory = 'wardrobe.lock.d'):
		"""
		Initialize a new locker that will use the directory in the system's
		temp directory for locking.
		
		If locknow is set, the lock will be requested instantly; creating an
		instance will fail if it can not be acquired.
		"""
		self.path = directory
		self._locked = False
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
			os.mkdir(self.path)
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
		os.rmdir(self.path)
		self._locked = False
		return True

	def lock(self):
		"""
		Acquire the lock.
		
		If already locked, a StateError is raised. If the lock could not be
		acquired, an AcquireError is raised. Return True.
		"""
		if self.locked:
			raise self.StateError('already locked, cannot lock again')
		return self._lock()

	def lockIfUnlocked(self):
		"""
		Acquire the lock if this instance is not already holding one.
		
		If a lock is already held, return True. If not, one is acquired and True
		is returned. If acquiring fails, an AcquireError is raised.
		"""
		# Don't lock again if we already own a lock.
		if self.locked:
			return True
		return self._lock()

	def unlock(self):
		"""
		Release the lock.
		
		If not locked, a StateError is raised. If the lock can not be released,
		an error (most likely OSError) is raised. Return True.
		"""
		if not self.locked:
			raise self.StateError('not locked, cannot unlock')
		return self._unlock()

	def unlockIfLocked(self):
		"""
		Release the lock if this instance is holding one.
		
		If no lock is held, return True. Else, behave like unlock(), except that
		no StateError will be raised.
		"""
		if self.locked:
			self._unlock()



class Place(object):
	"""
	A source or destination path, possibly on a remote system.
	
	This class is not to be used directly. Instead, use Source or Destination.
	"""

	def _getstring(self):
		"""
		The user@host::/directory string to be passed to rdiff-backup.
		
		Read-only.
		"""
		if isinstance(self.directory, str):
			directory = self.directory
		else:
			directory = self.defaultdir
		if isinstance(self.user, str):
			if isinstance(self.host, str):
				return '%s@%s::%s' % (self.user, self.host, directory)
			else:
				raise SettingCombinationError('user without host')
		else:
			if isinstance(self.host, str):
				return '%s::%s' % (self.host, directory)
			elif isinstance(self.directory, str):
				return directory
			else:
				raise SettingCombinationError('no settings specified')

	string = property(_getstring)

	def __init__(self, directory=None, host=None, user=None):
		self.defaultdir = '/'
		self.directory = directory
		self.host = host
		self.user = user

	def __repr__(self):
		return self.string



class Source(Place):
	"""A source path, possibly on a remote system."""



class Destination(Place):
	"""A destination path, possibly on a remote system."""
