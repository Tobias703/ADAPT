# Local Deployment

This section describes, how you can host a pluggable transport locally. This is meant as a test deployment, as PT-client and PT-bridge are both running on the client machine. This would not make any sense in an actual deployment scenario. For proper deployment, you can look into either the [Shadow Section](../shadow/shadow.md), which discusses deployment in the Shadow Network Simulator and as such requires a clean and proper deployment. Alternatively, the section on [Docker Deployment](../docker/docker.md) is also close to an actual deployment, since the PT-Environment is containerised and as such forced to be configured as if it were in an actual Network.

!!! note
    this is meant as an example for completeness sake. The deployment, as shown below, can either be modified into an actual deployment (by splitting it between two physical machines) or be executed as-is to show that/how the PT works in a live demo. For development and testing, Shadow is the preferred way of running a PT, since it is deterministic and less flaky. Shadow can also be used for live demos and is more robust then a local deployment.

## Prerequisites

For running a Pluggable Transport, there are only two prerequisites:

**Tor**: As discussed in the [Basics](../basics/running-a-pt.md), the newest version of `tor` is required to execute a PT. To download the actual newest version of Tor, do not blindly trust package managers like `apt`, but instead refer to the official download manual: <https://support.torproject.org/little-t-tor/getting-started/installing/>

**A PT**: This project mainly uses the `lyrebird` binary, which ships the `obfs` suite of Pluggable Transports. All examples will use `lyrebird` and will have to be reconfigured to the individual PT that is to be tested.

## Running the Client

Running the client is very straightforward. It is assumed, that `client-torrc` is a torrc, that is correctly configured to run Tor as a PT-client through the correct PT. For more details on how to configure the torrc correctly, you can either look into this project's `/src/client-torrc` file, which is a working example of such a configuration, or you can refer to [the section on the client torrc](../deployment-independent/torrc-client.md).

To run the PT using this config, simply execute the following command to run Tor with the provided config, assuming the config is in the directory, the command is being called from: `tor -f ./client-torrc`

## Running the Bridge

Running the bridge is equally easy. It is once again assumed, that `bridge-torrc` is a torrc, that is correctly configured to run Tor as a PT-bridge through the correct PT. For more details on how to configure the torrc correctly, you can either look into this project's `/src/bridge-torrc` file, which is a working example of such a configuration, or you can refer to [the section on the bridge torrc](../deployment-independent/torrc-bridge.md).

To run the PT using this config, simply execute the following command to run Tor with the provided config, assuming the config is in the directory, the command is being called from: `tor -f ./bridge-torrc`
