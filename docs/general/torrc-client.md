# torrc configuration for a PT-client

```yaml
# The "pt client" refers to the instance of Tor defined here; the "pt client binary" refers to the binary that actually contains the pt

DataDirectory ./ptclient # A place to save our fancy data

# Use the PT
UseBridges 1 # Yes, we want to use a bridge
ClientTransportPlugin obfs4 exec ../../../lyrebird # Name of the transport and path to the transport binary
Bridge obfs4 100.0.0.10:1234 BCC0C43EBEF9309D93D5DA52EDBC6C1F3528319E cert=wgYphbK4qjxy/AC9vpZoAsdwg4hWKC1yQxbFQZa1GYYBBCdGu07GBP0T3A+cRwBAPEk8CQ iat-mode=0 # This speaks the custom protocol, sits inbetween pt client and bridge binaries. Added credentials of the bridge for obfs4

#Port for Connection
SocksPort 127.0.0.1:9052 # The tor client uses this to connect to the pt client

# Disable Conflux (effectively just removes the "just one bridge" warning)
ConfluxEnabled 0

# Log debug file ./tor-client-debug.log
```
