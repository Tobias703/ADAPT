# Basics and general information

This page shows some general information that is needed to understand and successfully implement a Tor Pluggable Transport. It will start with the bare basics and build from there.

## What is a Pluggable Transport and how does it work?

This chapter should give you a basic idea of what Pluggable Transports (PTs) are and how they work. The most recent, full Pluggable Transport Specification dives into a lot more details. It can be found here:

[https://github.com/Pluggable-Transports/Pluggable-Transports-spec](https://github.com/Pluggable-Transports/Pluggable-Transports-spec)

A Pluggable Transport (PT) is a way to circumvent censorship. The main idea of PTs is that everyone can easily implement their own communication protocol, which is meant to make it harder for censors to spot Tor traffic. This depends on how well the PT is implemented, since the custom protocol could also be very easy to detect if not properly implemented. Using publicly available pluggable transports is also possible. The lyrebird binary for example ships the obfs suite. PTs are not directly part of the Tor network. They consist of a client and a bridge, where the client lives on the user's machine and talks to the bridge, which is a server that is able to communicate with the Tor network.

### How does it Work?

Looking at the Pluggable Transport as a whole, it has four points of communication plus two between the Tor binary and the client and target resources:

- An application talking to the Tor binary on the Client machine
- The Tor binary talking to the PT-client on the Client machine
- The PT-client talking to the PT-bridge
- The PT-bridge talking to the PT-client
- The PT-bridge talking to the Tor binary on the server
- The Tor binary talking to the Tor network on the server

The communication between PT-client and PT-Bridge can technically be seen as a single point of communication, it is listed here twice to clarify the points of interaction for both client and server instead of treating the two components as one.

### Typical connection flow

**Local Application <-> local Tor binary:** Accepts incoming connections from local software like a browser. This can be done using a SOCKS connection. This project exclusively uses a SOCKS5 connection via port 9052 to connect the PT-client to whatever application wants to make use of it. This is configured in the torrc for the PT-client. For testing connection to the Tor network, users can either install a Plugin like FoxyProxy in Firefox and connect it to 127.0.0.1:9052 via SOCKS5, or configure that same address as a Bridge inside the Tor-Browser. To verify if the Pluggable Transport is working, visit: [https://check.torproject.org/](https://check.torproject.org/)

**local Tor binary <-> PT-client:** The Tor binary talks to the Pluggable Transport binary via the [Pluggable Transport Specification](https://github.com/Pluggable-Transports/Pluggable-Transports-spec). For that, the Pluggable Transport binary is called from the torrc of the PT-client along with the pluggable transports that the client wants to use. This is done via the `ClientTransportPlugin` configuration. This config is followed by the name of the PT to be called, followed by `exec` and the path to the PT binary.

**PT-client <-> PT-bridge:** The PT-client and PT-bridge talk to each other using the PT's custom protocol. As such, they both have to use the same PT. These protocols can be completely arbitrary and for example include obfuscation or data smuggeling. To configure this connection for the PT-client, the option `Bridge` is used. It contains the name of the PT that is to be used, as well as the IP of the bridge using said PT (hostnames not supported, has to be an IP address) and the port of the pluggable transport. For authenticated transports like obfs4, you also have to provide credentials like identity, key and iat-mode. The PT-bridge is configured with the `ServerTransportListenAddr`, which is followed by the name of the PT that is to listen on the specified port and finally the listen address, which is it's own IP and the port that is to be listened on. This should be the same as configured in the client.

**PT-bridge <-> bridge Tor binary:** The Tor binary talks to the Pluggable Transport binary via the [Pluggable Transport Specification](https://github.com/Pluggable-Transports/Pluggable-Transports-spec). For that, the Pluggable Transport binary is called from the torrc of the PT-bridge along with the pluggable transports that the bridge wants to serve. This is done via the `ServerTransportPlugin` configuration. This config is followed by the name(s) of the PT(s) to be called (seperated by commas if it's more then one), followed by `exec` and the path to the PT binary. Remember, that a single PT binary can include several Pluggable Transports. The lyrebird binary for example ships the obfs2, obfs3 and obfs4 PTs.

**bridge Tor binary <-> Tor Network:** The server is assumed to be in a non-censored network. As such, its Tor binary bootstraps into the Tor network independently of the PT logic.
