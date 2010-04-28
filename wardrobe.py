#!/usr/bin/env python

import atexit
import errno
import os
import re
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



class SDGenerator(object):
	"""
	Given some data (usually a string), generate a Source and Destination pair.
	
	This class is not to be used directly. Instead, use one of the derived
	classes or develop your own.
	"""

	def __init__(self):
		raise NotImplementedError('has to be subclassed')



class PullCompleteHost(SDGenerator):
	"""
	Source and Destination generator for pulling backups of complete hosts.
	
	A common scenario is "iterate over hosts a, b and c and pull backups of
	their root directory, storing them in /var/backup/{a,b,c}". This class
	generates Source and Destination for such a scenario. If your host names
	contain unusual characters, the regex property allows you to substitute
	those when generating the destination directory.
	"""

	def _getregex(self):
		"""
		The RegexObject that is used for finding substrings in the source name
		that should be replaced by substitute.
		
		You may set this property to anything re.compile() understands (most
		importantly, strings and already compiled regexes).
		
		Defaults to '[^A-Za-z0-9.-]'.
		"""
		return self._regex

	def _setregex(self, value):
		self._regex = re.compile(value)

	regex = property(_getregex, _setregex)

	def _getsubst(self):
		"""
		The string that will replace substrings matched by regex.
		
		Defaults to '_'.
		"""
		return self._subst

	def _setsubst(self, value):
		if not isinstance(value, str):
			raise TypeError('subst has to be a string')
		self._subst = value

	subst = property(_getsubst, _setsubst)

	def _getbasedir(self):
		"""
		The base directory to store backups in.
		
		The host name passed to generate() will be used to construct a
		subdirectory name. The final destination will then be the concatenation
		of base directory and subdirectory.
		
		When setting this property to a relative path it will automatically be
		qualified to an absolute one by prepending the current directory.
		"""
		return self._basedir

	def _setbasedir(self, value):
		if not isinstance(value, str):
			raise TypeError('basedir has to be a string')
		if os.path.isabs(value):
			self._basedir = value
		else:
			self._basedir = os.path.abspath(value)

	basedir = property(_getbasedir, _setbasedir)

	def _getuser(self):
		"""
		The user to connect to the remote host as.
		
		Defaults to None, which means that no user name will be supplied to
		rdiff-backup, which will in turn not supply a user to ssh. ssh will then
		either use the name configured in ~/.ssh/config or the current user.
		"""
		return self._user

	def _setuser(self, value):
		if not (isinstance(value, str) or value is None):
			raise TypeError('user has to be a string or None')
		self._user = value

	user = property(_getuser, _setuser)

	def __init__(self, basedir, user=None):
		"""
		Initialize a new generator that will use the given basedir to save
		backups in.
		
		You may supply user as a convenience.
		"""
		self.basedir = basedir
		self.user = user
		self.regex = '[^A-Za-z0-9.-]'
		self.subst = '_'

	def generate(self, host):
		"""Generate a Source and Destination pair for the given host."""
		s = Source('/', host, self.user)
		d = Destination(os.path.join(self.basedir,
		                             self.regex.sub(self.subst, host)))
		return (s, d)
