# Configuring Shadow

Shadow consists of three (or two) main configuration parts. These are the `shadow.yaml` config file, the `topology.gml` graph for defining the network's topology (which can also be within the `shadow.yaml`, but separating the two is cleaner) and finally the `shadow.data.template` directory, which includes all client specific configurations for each of the devices within the shadow network.

## shadow.yaml

This is the main configuration file for shadow. It contains information about how the simulation is supposed to run. This includes: Simulated time for the simulation to run (executes much faster then the defined time, since it is simulated time), topology, hosts in the network, what each host executes and when they execute it and which network node each host is associated with. The full shadow config specification can be found here: [https://shadow.github.io/docs/guide/shadow_config_spec.html](https://shadow.github.io/docs/guide/shadow_config_spec.html)

## topology.gml

This file defines the topology of the network. It includes all of the nodes and edges that define the structure of the network and how each node can reach each other node. This could be included in the `shadow.yaml` file but is separated into it's own file for a cleaner implementation. The specification for shadow network topologies can be found here: [https://shadow.github.io/docs/guide/network_graph_spec.html](https://shadow.github.io/docs/guide/network_graph_spec.html)

## shadow.data.template

This is a directory which contains all of the configuration files for each of the hosts in the network. Shadow simulates these hosts with their own simulated file system and outputs the simulation result in a `shadow.data` directory. The `shadow.data.template` directory is used by shadow to initialize the `shadow.data` directory. This way you can easily allow a host to access something like a config file by copying the file into the host's template directory. A host can also access files outside it's own template directory, for example by navigating up and out of it's template dir but in order to keep a clean and separated codebase, this should only be done to avoid large and redundand files. The only file the hosts share in the current setup is the lyrebird binary for executing the pluggable transport since that binary is a rather large file and can be in this project only once by sharing it between hosts.
