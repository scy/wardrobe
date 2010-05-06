wardrobe — a wrapper for rdiff-backup
=====================================

_wardrobe_ aims to be a nice wrapper around
[rdiff-backup](http://rdiff-backup.nongnu.org/). It is primarily designed for
system administrators having to automatically backup several hosts.

You may think of _wardrobe_ as a framework, providing
[Python](http://python.org/) classes for defining backup settings and managing
_rdiff-backup_ runs. It helps you define templates for host groups and perform
regular backups of any number of machines.

It is not a command that takes a configuration file. Instead, it is a set of
classes; _you_ write the command that actually does your backups, utilizing the
_wardrobe_ classes which take care of the low-level details.


FAQ
---


### Why is it called “wardrobe”? ###

Because that word contains __r__, __d__ and __b__ (for _rdiff-backup_) in the
right order.


### Is it stable? ###

We are currently finding out. You may want to consider it “beta” code.


### How do I use it? ###

We will add examples in a few days.


### What are its requirements? ###

_rdiff-backup_ and Python 2.5 should be sufficient.


### What license is it available under? ###

The 3-clause BSD license, please have a look at the `LICENSE` file. If you need
another license, talk to us.


### I have found a bug! ###

Please [report it at GitHub](http://github.com/dotsunited/wardrobe/issues).


### May I contribute? ###

Yes, absolutely.


### Who are you? ###

We are [Dots United](http://www.dotsunited.de/). We build web sites. And we do
regular backups of our servers. That’s why we develop _wardrobe_.
