# Shadow Network Simulation

The Shadow Network Simulator is a tool, provided by the Torproject. It is meant to emulate a Tor network in a deterministic fashion. As such, it is easy to test a Pluggable Transport using Shadow.

## How does Shadow work?

Shadow simulates a network by creating a virtual network and running binaries inside said network. This way, shadow can call processes on the host machine without any setup concerning containerization while still being able to have control over the entire network. The most important piece of control, Shadow has over the network is the network time. Shadow lets you define for "how long" the simulation should run and at which point in the simulation events are supposed to happen. The simulation, however, does not run in real time but in simulated time and as such can finish a lot faster then the configured time to run the simulation.

### Terminology

|Term|Explanation|
|-|-|
|**Graph:**|The simulated Network within shadow is defined via a graph. The graph describes how the network looks. It consists of nodes and edges. The graph is defined in the `topology.gml` file within shadow.|
|**Edge:**|Edges connect nodes. They can be used to define connection quality aswell, such as bandwidth, latency and packet loss.|
|**Node:**|A device in a network is always associated with a node. Using edges to connect these nodes, it allows the user to define, which devices/nodes can communicate with which other devices/nodes and what the quality of this connection is. Several different devices in the simulation can be defined as the same node. Each node has a loopback edge, meaning it can communicate with "itself". Thus, several devices under the same node can be seen as something akin to a local network, while different nodes are different networks, connected by edges.|
|**Simulation time:**|Shadow simulates a network. You can define for how long this simulation is supposed to run. This duration, however, is not a representation in real time but rather in simulation time. This means, if a 10 minute simulation time is specified, the simulation can finish in a few seconds but each host in the network will think and act like 10 minutes have actually passed. Whenever the term "simulation time" is used, it is thus referred to the time a host within the simulation thinks has passed, and not the actual physical time that has passed.|

### Components

This section describes all the moving parts within shadow to convey a better understanding about what files shadow uses and what each of them does. For this, a brief overview of the folder layout within this project is given first, followed by rough descriptions about what each component does. For further details about the configuration and config files within shadow, please refer to the [configuration](./configuration.md) page.

```yaml
shadow/
    conf/                           # A ton of shadow configuration. Taken directly from the examples in the Shadow Git repo.
        [...]
    shadow.data/
        [...]
    shadow.data.template/           # Config for all the nodes in the Shadow network, many taken from the examples in the Shadow Git repo.
        [...]
    lyrebird                        # The executable for lyrebird, a pluggable transport implementing obfs3 and obfs4.
    run_shadow.sh                   # Convenience script for running the shadow simulation. Automatically clears the last simulation for a clean re-run.
    shadow.yaml                     # The main configuration for the Shadow simulator. Includes a description of each node and what they do.
    topology.gml                    # The Topology of the Shadow network. Defines which nodes exist and can talk to whom.
```

**conf:** The `conf` directory includes a lot of configuration files for setting the hosts up for shadow. It includes preconfigured `torrc` files for different roles in a Tor network (like authority server, client, exit nodes, etc.). This entire directory is taken straight out of the Shadow GitHub repository, available here: <https://github.com/shadow/shadow/tree/main/examples/docs/tor/conf>. This folder can, if needed, be updated to the newest version but should generally be left untouched as this is configuration straight from shadow.

**shadow.data:** This directory is the output of the shadow simulation. Shadow does not delete this directory when running a new simulation, hence, it always needs to be deleted before running shadow. The `run_shadow.sh`-script automatically deletes this directory and runs the shadow simulation. Deleting this directory is usually always safe since the shadow simulation is deterministic and running the simulation should restore the directory exactly as it was, as long as no simulation parameters were changed.

**shadow.data.template:** The template directory for `shadow.data`. Everything within this directory gets copied into `shadow.data` at the start of the simulation. This way, hosts within the network can easily be configured by writing their initial configuration files into the respective template directories.

**lyrebird:** The lyrebird binary ships the obfs suite of pluggable transports. In this project, we are using obfs3 and obfs4 inside shadow. This binary is in the `shadow` directory, because several hosts need to access it and pasting it into each of their template directories would be redundand for such a large file. This binary ships with the Tor Expert Bundle, which can be downloaded here: <https://www.torproject.org/download/tor/>

**run_shadow.sh:** As already mentioned, this is a convenience script for running shadow, so that the simulation is guaranteed to be correctly executed with a single call of this script. It deletes the `shadow.data` directory and runs the simulation from the correct source.

**shadow.log:** This directory shows the entire detailed log of the shadow simulation, once it has run. This log is semi-useful. If there is an issue in the simulation, logging can be enabled in the affected host's `torrc` config file, which is much more useful for debugging any issues.

**shadow.yaml:** This is the main config file for shadow. It defines all the hosts in the simulation as well as parameters like simulation time etc.

**topology.gml:** This file represents the network topology of the simulation. It defines, which host can talk to which other host on the network.

## Why use Shadow?

|||
|-|-|
|**Determinism:**|The main motivation for using shadow is the deterministic nature of the simulation. Running a pluggable transport in the real Tor network can often yield unexpected problems, such as very long bootstrapping times. It is not entirely clear why, but pluggable transport clients sometimes take more then ten minutes to bootstrap into Tor. With shadow, this process can deterministically be reduced to seconds.|
|**Speed:**|As already mentioned, running the simulation is usually a lot quicker then bootstrapping into the actual Tor network.|
|**Persistent and accurate end state:**|After running the simulation, one can store away the results of said simulation, along with all the information they could ever need. Detailled logs and pcaps are easily accessible for each host and can be used for straightforward debugging. No important information is lost as compared to locally running the PT|
|**Non-persistence:**|Once the simulation is set up and the initial data for each host is loaded, running the simulation will delete all data from previous runs and thus keep the simulation from failing due to a previous run resulting in a broken state of any of the hosts.|
|**Accuracy:**|Because shadow is an accurate simulator of the Tor network, it quickly complains about any issues within the given configuration. This can even catch issues you wouldn't notice during deployment in the Tor network and forces users to adhere to best practices, even if different implementations would technically work aswell.|
