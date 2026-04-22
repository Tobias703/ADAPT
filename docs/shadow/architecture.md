# This Project's Shadow Architecture

To help understand the specific implementation of the Shadow Simulator in this project, the following sections will describe the exact architecture, topology and nodes used in the current Shadow setup.

## Topology

To get started, we will have a look at the Topology of the Network. This includes all nodes in the network, as well as the edges connecting them. The exact definition of the Topology can be found and edited in the `topology.gml`-file.

### Nodes

There are currently three different nodes in the network. Remember that several hosts can be the same node, so each node can technically be treated like its own Network of Hosts. These nodes are:

**Censored Hosts (ID 0):** Hosts that are assigned Node 0 are supposed to be inside a censored network. These are clients, that want to access a resource in another network. The Network around them, however, does not let them reach their target resource directly.

**Bridge (ID 1):** There is currently only one Host associated with ID 1. This is the Bridge. The Bridge is the only host that is both reachable out of the censored network and able to access the free network.

**Free Network (ID 2):** The free network is supposed to be the "uncensored" space. The target resource for the hosts in the censored network resides here. In addition to that, a bunch of Hosts that together form a small-scale Tor-Network are also associated with this Node ID to emulate the Tor network.

### Edges

The edges are connected in the way you would assume with only a few minor noteworthy details:

- The nodes all have a connection defined with 100 Mbit up- and download speeed, a latency of 10 ms and no packet losses ever.
- Every node has an edge to EVERY other node, including themselves (so that Hosts under the same node can communicate amongst themselves)
- Removing the edge between nodes 0 and 3 would not work to make node 0 unable to access resources from node 3, since it would just jump over node 2. To emulate censorship, the edge between nodes 0 and 3 is defined as having a latency of only 1 ms to make it attractive for routing but it has a packet loss of 100%.

As you might have gathered from this topology, there is no actual proper censorship going on in the network. Any arbitrary proxy route over node 2 would give unrestricted access to the 'free' network. This is merely meant to demonstrate that the PT is working and regular connections are not possible.

## Hosts

Now that we know what the network looks like, we can have a look at the specific implementation of each of the important hosts in the network and what exactly they do. The hosts are defined within the `shadow.yaml` file.

### Node 0

Node 0 currently consists of two hosts:

- **client3:** client3 is supposed to be a client, that is using obfs3 to connect to the bridge and access the target resource. It has the IP address 100.0.0.3. It launches 4 processes:
    - An instance of Tor that tries to connect to the Tor-network as-is
    - An instance of curl that tries to fetch the target resource as-is
    - An instance of Tor that connects to the bridge via obfs3
    - An instance of curl that tries to fetch the target resource via a SOCKS5 proxy using the Pluggable Transport instance of Tor
- **client4:** client4 is, as you might have guessed, a client using obfs4 to connect to the bridge and access the target resource. It has the IP address 100.0.0.4. It launches the same 4 processes as `client3` with the only difference being, that it implements credentials in the torrc to authenticate via obfs4 at the bridge:
    - An instance of Tor that tries to connect to the Tor-network as-is
    - An instance of curl that tries to fetch the target resource as-is
    - An instance of Tor that connects to the bridge via obfs3
    - An instance of curl that tries to fetch the target resource via a SOCKS5 proxy using the Pluggable Transport instance of Tor

### Node 1

Node 1 currently consists of one host:

- **bridge:** The bridge sits inbetween the censored and free network, having access to both. It can successfully bootstrap into the Tor network inside Node 2 and has the IP address 100.0.0.1. It only runs one process:
    - An instance of Tor that exposes both obfs3 and obfs4 for the two clients to connect to

### Node 2

Node 2 currently consists of eight hosts. Seven of these hosts are taken directly out of the [shadow examples](https://github.com/shadow/shadow/tree/main/examples/docs/tor). They will be listed very briefly but not described in further detail. The only important host associated with node 2 is the `target`, which holds the resource, `client3` and `client4` want to access. The specific description is as follows:

- **4uthority:** There is one Authority server to manage the Tor network
- **exit1 & exit 2:** There are two exit nodes out of the Tor network
- **relay1, relay2, relay3 & relay4:** There are four relay nodes to wire the Tor network internally
- **target:** The target is a simple webserver running at IP 100.0.0.20. It is running two processes:
    - A simple python-webserver serving only the string "Fetched target resource successfully\n". This can be used to verify if the clients have successfully fetched the target.
    - A Tor hidden service to enable the clients to fetch the contents of the python webserver via the Tor network.

## Important files

Usually, all files that a Host is using is found in its respective directory inside `./shadow.data.template/hosts`. In this section, any noteworthy additional files will be listed.

**lyrebird:** The lyrebird binary, found in the root of the shadow directory, is the pluggable transport binary that the two clients as well as the bridge are using. It is in the root directory of shadow since the simulation result is a copy of the template folder. Copying a 16.7 MiB file for two clients and a host would be unnecessary clutter so it is left out of the template directory.

**./conf/\*:** The `./conf` directory holds configuration that is needed to run a Tor network of such a small, simulated scale. It is taken from the [shadow examples](https://github.com/shadow/shadow/tree/main/examples/docs/tor) as-is and should not be modified unless you REALLY know what you're doing. But then, why are you reading this here document?

**./shadow.data.template/somescript.sh:** The scripts in the template directory are merely used to clarify the simulation output. As you might have noticed, some hosts like the clients call several instances of the same service (like two instances of Tor or curl). The output logs would usually be two files called something like `tor.1000.stdout` and `tor.1001.stdout` with no way of telling which instance is which without going through the logs. If the services are, however, called via these scripts, their names will instad include the script name thus making the output a lot clearer.

**shadow_run.sh:** A simple bash script to delete the old simulation results and immediately run shadow. Convenience to reduce command size to run Shadow.

**docker_run.sh:** Similar to `shadow_run.sh` but instead of running Shadow locally, it runs Shadow under docker so you do not even have to install anything apart from docker.
