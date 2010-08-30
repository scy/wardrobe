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

I am currently finding out. You may want to consider it “beta” code.


### How do I use it? ###

Please have a look at `twohosts.example.py` for a simple example. It covers most
of _wardrobe_’s current features.


### What are its requirements? ###

_rdiff-backup_ and Python 2.5 should be sufficient.


### What license is it available under? ###

The 3-clause BSD license, please have a look at the `LICENSE` file. If you need
another license, talk to us.


### I have found a bug! ###

Please [report it at GitHub](http://github.com/scy/wardrobe/issues).


### What features are you planning to add? ###

  * Introduce a queueing mechanism that allows you to iterate over a number of
    hosts without having to write the loop yourself.

  * Add some simple scheduling to that mechanism to enable constructs like
    “only consider hosts which have not been backed up for five hours or longer”
    or “only consider the host which has been least recently backed up”.

  * Make some things possibly more convenient to write.


### May I contribute? ###

Yes, absolutely.


### Who are you? ###

I am [Tim Weber](http://www.scytale.name/). I’m a web developer and server
admin. And I do regular backups of servers and workstations. That’s why I
develop _wardrobe_.

The basic functionality of wardrobe has been developed during the six months I
was working at [Dots United](http://www.dotsunited.de/). They allowed me to
take over the project and continue to work on it in my spare time.


### How do I contact you? ###

Please use the messaging feature of GitHub or the
[issue tracker](http://github.com/scy/wardrobe/issues).
