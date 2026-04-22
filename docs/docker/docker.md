# Docker Deployment

This section will describe, how to run a PT using docker. For this, there is a predefined docker setup in this project which will take care of almost everything. This form of deployment does not make a lot of sense for development or testing, since the containerized environment is more difficult to debug. For that purpose, the [Shadow deployment](../shadow/shadow.md) is still the preferred way of doing things.

!!! note
    This deployment is an example and as such held entirely on the local machine. For a production deployment using docker, the configurations have to be altered and the PT-client/PT-bridge containers have to be run seperately on different machines!

## Prerequisites

There are only two (/three) prerequisites, required to execute the containerized Pluggable Transport:

**`docker` and `docker compose`**: If you are thinking about a docker deployment, you will most likely have these installed already. The reason why they are needed should be self-explanatory.

**A PT**: This project mainly uses the `lyrebird` binary, which ships the `obfs` suite of Pluggable Transports. All examples will use `lyrebird` and will have to be reconfigured to the individual PT that is to be tested.

## Configuring the Pluggable Transport

Before running the PT, you will first want to configure it. By default, the docker implementation is built to use the lyrebird binary and connects via the obfs3 transport. To change that, you'll need to do two tings for client AND bridge:

1. **Swap the used binary:** In the dockerfile, there is the following line: `COPY --chown=toruser:toruser /shadow/lyrebird /usr/local/bin/lyrebird`. Change the `/shadow/lyrebird`-path to the path to any binary you want to use. As you might have noticed already, this path's root is the root of this project. Do this for the dockerfile of the client and the bridge.
2. **Configure the torrc files to use the correct transport:** The torrc files for client and server are in their respecitve directories under `./docker_deployment/client/` and `./docker_deployment/bridge/`. Change the config here. If you have swapped the binary in step `1.`, you'll have to change the name of the binary in the `ClientTransportPlugin` and `ServerTransportPlugin` lines of the torrc files respectively. Now you'll just have to change the name of the transport used in the `ClientTransportPlugin`, `ServerTransportPlugin`, `ServerTransportListenAddr` and `Bridge` lines. Done.
3. Depending on if you have already built the containers, you might want to rebuild them for the changes to take effect. To do this, simply run `docker compose build`

## Running the Pluggable Transport

To run the Pluggable Transport docker deployment, you simply have to navigate into the `docker` directory at the root of this project and run the command: `docker compose up -d` to run the containers in detached mode.

The `client-logs.sh` and `bridge-logs.sh` scripts can be used to inspect a live view the logs of the client and bridge, respectively.

## Known Problem

There is one known and currently unfixable problem with the deployment. In the `docker-compose.yml`, there are static IP addresses defined for each container in the network. The reason for that is, that the torrc files cannot resolve hostnames and must have IP addresses defined within them. To fix this issue, there would have to be an automated process in the lifetime of the containers, which resolves the hostname of the other container and insert that into the torrc before running the PT. This would add a lot of complexity and is left out for simplicity.

If there is an error with the address space of the containers, make sure to delete any docker networks which might conflict with the address space, defined in the `docker-compose.yml`. An alternative would be to change this address space. This would, however, also require to edit the torrc files for client and bridge container.
