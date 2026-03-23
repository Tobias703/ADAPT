# Running a Pluggable Transport

In order to run a Pluggable Transport, one must first understand, how PTs are implemented and how they are called.

## What does a production-ready PT look like?

A PT is usually shipped in form of a binary/executable. This binary however, is **not** supposed to be run as local software/executed as-is. Instead, it is supposed to be called and opened by an instance of Tor.

### Why run it through Tor?

As already mentioned in the [Basics](basics.md), a PT communicates via the Pluggable Transport Specification. This means, that you must call the PT with a piece of software that is also communicating with the most recent PT-Spec. This piece of software is Tor. So in order to run a PT, an instance of Tor has to simply be configured to use said PT. The rest is done automatically, communicated over the PT-Spec. Tor handles all Tor-specific logic, while the PT handles the communication between the client- and server-instances of the PT with the desired protocol/method of communication.

### How to run it through Tor

As described above, to run a pluggable transport through Tor, a valid configuration file has to be provided when Tor is called. The basic command is: `tor -f path-to-config` where the path to the config can either be a relative path from where the command is called, or an absolute path. The `config` file will from here on out be referred to as a `torrc`-file or just a `torrc`. The reason for that is, that if no configuration file is provided, Tor uses a file called `torrc` inside `/etc/tor/`. Documentation and examples list these files as having the word `torrc` in their titles for clarity. The same is done in this project. `torrc`-files do not have a file ending, have `torrc` as either their name or part of their name and are opened as textfiles. They contain configuration for Tor to follow. For more details on `torrc`-files, refer to the [Deployment Independent Documentation](../deployment-independent/deployment-independent.md).

#### Running a PT-client

To run a PT-client, the torrc has to include the following:

- A `DataDirectory [path]` to store the state of the PT during operation and after shutdown
- `UseBridges 1` to tell tor, that it should use a bridge (the PT-server is a bridge)
- The `ClientTransportPlugin [pt-name(s)]`, which tells Tor, where the PT-binary is and which Pluggable Transport the PT-binary has to use as some binaries ship several Pluggable transports
- A `Bridge [pt-name] [ip:port]` line, which describes which PT has to use which bridge and what IP address and port for the bridge is
- A `SocksPort [ip:port]` for local applications to connect with the Pluggable Transport

Using these parameters, Tor can successfully enable local software to connect to the Pluggable Transport and the PT to connect to its bridge and to communicate into the Tor-network if the config is correct and the bridge is correctly set up and running. For detailled information and an example of a `client-torrc`, refer to the [section regarding the Client torrc](../deployment-independent/torrc-client.md)

#### Running a PT-bridge

A PT-bridge takes a bit more configuration, since it has to talk to the Tor-network in addition to the PT-client and not just to a local application. The required parameters are:

- A `DataDirectory [path]` to store the state of the PT during operation and after shutdown
- The `ServerTransportPlugin [pt-name(s)] exec [path_to_pt-binary]`, which tells Tor, where the PT-binary is and which Pluggable Transport the PT-binary has to use as some binaries ship several Pluggable transports
- The `ServerTransportListenAddr [pt-name] [ip:port]`, which defines the port on which the server should listen in order to recieve connections for the PT, listed in this option
- `BrigeRelay 1`, because the PT-bridge is, in fact, a bridge
- `Address [ip]` to define the bridge's ip-address
- `ORPort [port]` to define the Onion-Routing port for connections to Tor clients and servers
- `ExtORPort [ip:port]` opens the Extended ORPort for connections to the Pluggable Transport

Optional but strongly recommended:

- `PublishServerDescriptor 0` because publishing a server descriptor on a supposedly hidden bridge would be counterproductive.
- `BridgeDistribution none` because, once again, this is our own, private bridge and we do not want to distribute it.
- `SocksPort 0` to disable any non-bridge related connections
- `ContactInfo [name] [email-address]` to optionally provide Tor with information about how to contact you if something is wrong with the bridge

Using these parameters, Tor can successfully enable a PT-client to connect to its PT-server and its PT-server to connect to the Tor-network if the config is correct and the client is correctly set up and running. For detailled information and an example of a `bridge-torrc`, refer to the [section regarding the Bridge torrc](../deployment-independent/torrc-bridge.md)
