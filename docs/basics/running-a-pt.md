# Running a Pluggable Transport

In order to run a Pluggable Transport, one must first understand, how PTs are implemented and how they are called.

## What does a production-ready PT look like?

A PT is usually shipped in form of a binary/executable. This binary however, is **not** supposed to be run as local software. Instead, it is supposed to be called and opened by an instance of Tor.

### Why run it through Tor?

As already mentioned in the [Basics](basics.md), a PT communicates via the Pluggable Transport Specification. This
