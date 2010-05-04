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



class Defaultable(object):
	"""
	Stores a single value or points to another Defaultable.
	
	Using this class, you can cascade and template options: If you leave value
	unset, but point parent to another Defaultable, that Defaultable's value
	will be used when trying to read the value.
	"""

	def __str__(self):
		"""Return value.__str__()."""
		return self.value.__str__()

	_checktype = None
	"""If set to a type, value has to be an instance of this type."""

	def _getparent(self):
		"""
		The parent of this Defaultable.
		
		If this instance's value is unset, the value of the Defaultable
		referenced here will be used. If you set this property to None, there
		will be no parent and the local value will always be returned, even if
		it is None.
		"""
		return self._parent

	def _setparent(self, value):
		if not (isinstance(value, Defaultable) or value is None):
			raise TypeError('parent has to be a Defaultable instance')
		self._parent = value

	parent = property(_getparent, _setparent)

	def _getvalue(self):
		"""
		The value of this Defaultable, or that of its parent.
		
		When this property is written to, the instance's defaulting property
		will be set to False, even if you set the value to None. To use the
		default again, set defaulting=True.
		
		When defaulting evaluates to True, reading this property will return
		the value of the parent. Else it will return the stored value, or None
		if no value has been stored yet.
		"""
		if self.defaulting and not (self.parent is None):
			return self.parent.value
		else:
			return self._value

	def _setvalue(self, value):
		if isinstance(self._checktype, type) and \
			not isinstance(value, self._checktype):
			raise TypeError('value has to be a %s' % self._checktype.__name__)
		self.defaulting = False
		self._value = value

	value = property(_getvalue, _setvalue)

	def __init__(self, parentorvalue=None, checktype=None):
		"""
		Create a new Defaultable.
		
		You may supply a parent or a value as a convenience. They will be
		recognized by their type: Supply a Defaultable to set the parent,
		supply anything else to set the value. If you want to set the value to
		be a Defaultable, you have to set the value property explicitly.
		
		You may also supply a type. Setting this instance's value will then only
		succeed if the new value is an instance of the specified type. The type
		can currently only be set at construction time.
		"""
		if isinstance(parentorvalue, Defaultable):
			self.value = None
			self.parent = parentorvalue
			self.defaulting = True
		else:
			self.parent = None
			self.value = parentorvalue
			self.defaulting = False
		if isinstance(checktype, type):
			self._checktype = checktype



class Ternary(object):
	"""
	Representing three possible truth values: True, False and None (unknown).
	"""

	def _getvalue(self):
		"""
		Set or retrieve the ternary value.
		
		Deleting this value is not possible. Trying to do so will result in it
		being set to None.
		"""
		return self._value

	def _setvalue(self, value):
		if value not in (True, False, None):
			raise TypeError('value has to be True, False or None')
		self._value = value

	def _delvalue(self):
		self.value = None

	value = property(_getvalue, _setvalue, _delvalue)

	def __init__(self, value=None):
		"""
		Create a new Ternary.
		
		It will be initialized to None or the value you specify.
		"""
		self.value = value



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



class Filter(object):
	"""Base class for filter parameters passed to rdiff-backup."""

	def _getparams(self):
		"""
		A list of string parameters suitable for passing to rdiff-backup.
		
		Read-only, use the writable properties of the subclasses to set.
		"""
		raise NotImplementedError('has to be subclassed')

	params = property(_getparams)



class SingleFilter(Filter):
	"""Base class for single-value filter parameters."""

	def _getvalue(self):
		"""The value of this parameter (i.e. a path)."""
		return self._value

	def _setvalue(self, value):
		if not isinstance(value, str):
			raise TypeError('value has to be a string')
		self._value = value

	value = property(_getvalue, _setvalue)

	def _getparams(self):
		"""
		A list consisting of two strings: This parameter's name and its value.
		
		Read-only, use the value property to set the value.
		"""
		return ['--%s' % self._param, self.value]

	params = property(_getparams)

	def __init__(self, value):
		"""
		Create a new filter parameter.
		
		You have to specify the value the filter should have, i.e. a (possibly
		globbed etc.) path.
		"""
		self.value = value



class FilterSet(Filter):
	"""A class able to hold a number of filters, useful for grouping."""

	def _getparams(self):
		"""
		The flattened list of parameter name and value strings, suitable for
		passing to rdiff-backup.
		
		Read-only, use the extend() method to add new Filters.
		"""
		r = []
		for f in self._filters:
			r.extend(f.params)
		return r

	params = property(_getparams)

	def __init__(self, *args):
		"""
		Create a new FilterSet.
		
		You may pass any number of Filter instances or sequences of Filter
		instances as arguments.
		"""
		self._filters = []
		self.extend(args)

	def extend(self, *args):
		"""
		Add any number of Filter instances to the FilterSet.
		
		The args may either be Filter instances or sequences of Filter
		instances.
		"""
		for arg in args:
			# Check whether the argument is a single Filter instance.
			if isinstance(arg, Filter):
				self._filters.append(arg)
			else:
				# Check whether the argument is iterable.
				i = None
				try:
					i = iter(arg)
				except TypeError:
					# If it is not, it is nothing we allow to add.
					raise TypeError('attempt to add non-Filter, non-sequence type')
				if not i is None:
					# The argument is iterable. Recursively try to add it.
					for subarg in arg:
						self.extend(subarg)



class Exclude(SingleFilter):
	"""An --exclude parameter."""
	_param = 'exclude'



class ExcludeFilelist(SingleFilter):
	"""An --exclude-filelist parameter."""
	_param = 'exclude-filelist'



class ExcludeGlobbingFilelist(SingleFilter):
	"""An --exclude-globbing-filelist parameter."""
	_param = 'exclude-globbing-filelist'



class ExcludeRegexp(SingleFilter):
	"""An --exclude-regexp parameter."""
	_param = 'exclude-regexp'



class Include(SingleFilter):
	"""An --include parameter."""
	_param = 'include'



class IncludeFilelist(SingleFilter):
	"""An --include-filelist parameter."""
	_param = 'include-filelist'



class IncludeGlobbingFilelist(SingleFilter):
	"""An --include-globbing-filelist parameter."""
	_param = 'include-globbing-filelist'



class IncludeRegexp(SingleFilter):
	"""An --include-regexp parameter."""
	_param = 'include-regexp'
