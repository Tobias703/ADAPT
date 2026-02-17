# Basics and general information

This page shows some general information that is needed to understand and successfully implement a Tor Pluggable Transport. It will start with the bare basics and build from there.

## What is a Pluggable Transport and how does it work?

This chapter should give you a basic idea of what Pluggable Transports (PTs) are and how they work. The most recent, full Pluggable Transport Specification dives into a lot more details. It can be found here:

[https://github.com/Pluggable-Transports/Pluggable-Transports-spec](https://github.com/Pluggable-Transports/Pluggable-Transports-spec)

A Pluggable Transport (PT) is a way to circumvent censorship. The main idea of PTs is that everyone can easily implement their own communication protocol, which in turn makes it easier or harder for censors to spot tor traffic, depending on how well the PT is implemented. Using publicly available pluggable transports is also possible, like the lyrebird binary shipping the obfs suite. PTs are not directly part of the tor network. They consist of a client and a bridge, where the client lives on the user's machine and talks to the bridge, which is a server that is able to communicate with the tor network.