# torrc configuration for a PT-client

This page provides a working example for a torrc configuration regarding a PT-client. Each of the options has an explanation. The full specification was never moved to the new Tor-website. The old website however, still holds the specification and can be referenced to get detailled descriptions as well as a list of all possible configuration options. It can be found here:

<https://2019.www.torproject.org/docs/tor-manual.html.en>

```yaml
# The "pt client" refers to the instance of Tor defined here; the "pt client binary" refers to the binary that actually contains the pt

DataDirectory ./ptclient # A place to save the state of our PT-client

# Use the PT
UseBridges 1 # Yes, we want to use a bridge
ClientTransportPlugin obfs3,obfs4 exec ../../../lyrebird # Name of the transport and path to the transport binary; running the PT in client mode
Bridge obfs3 100.0.0.10:1235 # IP address and port of the obfs3 instance on the bridge. This speaks the custom protocol, sits inbetween pt client and bridge binaries. 
Bridge obfs4 100.0.0.10:1234 BCC0C43EBEF9309D93D5DA52EDBC6C1F3528319E cert=wgYphbK4qjxy/AC9vpZoAsdwg4hWKC1yQxbFQZa1GYYBBCdGu07GBP0T3A+cRwBAPEk8CQ iat-mode=0 # Same as above but for another transport and with added credentials of the bridge since obfs4 is an authenticated transport

#Port for Connection
SocksPort 127.0.0.1:9052 # This port is a local SOCKS5 proxy to use the PT (for example by the Tor Browser or Firefox via a local proxy)

# Disable Conflux (effectively just removes the "just one bridge" warning)
ConfluxEnabled 0

Log debug file ./tor-client-debug.log # This line will make the output of the bridge less verbose. Instead, a log file at the designated location will be generated, which is a LOT more verbose and can be used to better debug issues with a PT. This log file for example will include messages sent by the PT via stderr, which would usually not be displayed.
```
