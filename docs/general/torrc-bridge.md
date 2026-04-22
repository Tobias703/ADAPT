# torrc configuration for a PT-bridge

This page provides a working example for a torrc configuration regarding a PT-bridge. Each of the options has an explanation. The full specification was never moved to the new Tor-website. The old website however, still holds the specification and can be referenced to get detailled descriptions as well as a list of all possible configuration options. It can be found here:

<https://2019.www.torproject.org/docs/tor-manual.html.en>

```yaml
# The "pt bridge" refers to the instance of Tor defined here; the "pt bridge binary" refers to the binary that actually contains the pt

DataDirectory ./ptbridge # A place to save the state of our PT-bridge

# Disable Bridge IP Distribution
PublishServerDescriptor 0 # We do not publish our server descriptor, since this is supposed to be a private bridge
BridgeDistribution none # Neither do we distribute our bridge contact info for the same reason

# Define as Bridge, using a pt
ServerTransportPlugin obfs3,obfs4 exec ../../../lyrebird # Name of the transport and relative path to the transport binary; running the PT in bridge mode
ServerTransportListenAddr obfs3 100.0.0.10:1235 # IP address and port of the obfs3 instance on the bridge. This speaks the custom protocol, sits inbetween the pt-bridge and pt-client binaries
ServerTransportListenAddr obfs4 100.0.0.10:1234 # Same as above but for another transport
BridgeRelay 1 # Yes, we are a bridge

# Set up Networking
Address 100.0.0.10 # Hello, I'm the pt-bridge and this is my Address
ORPort 9111 IPv4Only # Onion Routing port, pumps raw data to and from pt bridge binary
ExtORPort 100.0.0.10:9051 # Extended Onion routing, control channel to talk to pt bridge binary. This is optional, since this communication has a fallback to the ORPort
SocksPort 0 # Disable SocksPort as this should not be used as a non-pt bridge

# Contact info so Tor does not complain
ContactInfo anonymous nobody@example.invalid # Put your contact info here if you are planning to run in production. For now it suppresses a warning about missing credentials.

Log debug file ./tor-bridge-debug.log # This line will make the output of the bridge less verbose. Instead, a log file at the designated location will be generated, which is a LOT more verbose and can be used to better debug issues with a PT. This log file for example will include messages sent by the PT via stderr, which would usually not be displayed.
```
