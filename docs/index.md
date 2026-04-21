# Index

This is the full documentation of ADAPT - Accelerated Development & Adaption of Pluggable Transports. It'll help you get started with developing Tor Pluggable Transports while trying to avoid as much Tor-Specific headaches as possible so you can focus on your Implementation and not be at the mercy of the Tor-Network having a good or bad day.

## Abbreviations

There are several terms and abbreviations used in this documentation. For clarity, they are listed here:

PT - Pluggable Transport

PT-client - The part of the PT, which is running on the user's machine

PT-bridge - In documentation also often referred to as 'PT-server', but for clarity in this project always referred to as 'PT-bridge' is the part of the PT, which is running on a server and acts as a bridge into the Tor network.

PPT - Python Pluggable Transport. This is name of the framework for easily building pluggable transports, implemented in this project.

## Where do I find what?

The documentation is split into several parts:

[The Basics](./basics/basics.md): This section talks about the theory behind Pluggable Transports and provides important foundational knowledge for implementing PTs.

[Project-Specific Information](./deployment-independent/deployment-independent.md): This section describes specific aspects of this project, which cannot be uniquely associated with one of the following sections. An example would be the torrc configurations used, since they vary very little between deployment types.

[Local Hosting](./local/local.md): Here's all the Info about locally hosting and using PTs.

[Docker](./docker/docker.md): Here's everything regarding PTs hosted fully under docker. Note that hosting a client under docker and a bridge locally and vice versa is possible.

[Shadow](./shadow/shadow.md): This is the full documentation for the Shadow Network Simulator. It provides developers with a very quick, easy and most importantly deterministic way of testing their PTs without having to rely on the whims of the Tor-Network.

[Python Pluggable Transport](./ppt/ppt.md): This piece of documentation contains information on the Python Pluggable Transport, which can either help you understand and implement Pluggable Transports in another programming language or implement a Pluggable Transport within the framework very quickly and easily (for simple transports in as few as 13 lines of code!).

## Project layout

The following shows the Layout of the Project. Relevant files have small comments behind them to tell you what they roughly are. Important files will have their documentation pages linked.

```yaml
.github/
├── workflows/
│   └── ci.yml                      # CI-Config for deploying the documentation page.
docker/
├── bridge/
│   ├── dockerfile                  # Dockerfile for the Tor Pluggable Transport bridge under Docker.
│   ├── entrypoint.sh               # Entrypoint script, executed by the container when it starts.
│   └── torrc                       # Tor config for the docker bridge.
├── client/
│   ├── dockerfile                  # Dockerfile for the Tor Pluggable Transport client under Docker.
│   ├── entrypoint.sh               # Entrypoint script, executed by the container when it starts.
│   └── torrc                       # Tor config for the docker client.
├── bridge-logs.sh                  # Live view of the docker bridge's logs.
├── client-logs.sh                  # Live view of the docker client's logs.
└── docker-compose.yml              # Compose file for easily starting the containers.
docs/
├── index.md                        # Full documentation title page.
├── setup_docs.sh                   # Setup script for when you want to change and deploy the docs locally. TODO: move to docs
└── [Further Documentation]
pythonPluggableTransport
├── transports
    ├── __init__.py
    ├── foobar.py
    └── invert.py
├── build.sh
├── config.py
├── ipc.py
├── main.py
├── ppt.spec
├── pt_client.py
├── pt_server.py
├── relay.py
├── socks5.py
├── test_pt.py
└── transport.py
shadow/
├── conf/                           # A ton of shadow configuration. Taken directly from the examples in the Shadow Git repo.
│   └── [...]                       
├── shadow.data.template/           # Config for all the nodes in the Shadow network, many taken from the examples in the Shadow Git repo.
│   └── [...]
├── lyrebird                        # The executable for lyrebird, a pluggable transport implementing obfs3 and obfs4.
├── run_shadow.sh                   # Convenience script for running the shadow simulation. Automatically clears the last simulation for a clean re-run.
├── shadow.yaml                     # The main configuration for the Shadow simulator. Includes a description of each node and what they do.
└── topology.gml                    # The Topology of the Shadow network. Defines which nodes exist and can talk to whom.
src/
├── bridge-torrc                    # Tor config for locally running the pluggable transport bridge.
├── client-torrc                    # Tor config for locally running the pluggable transport client.
├── run-bridge.sh                   # A script for locally running the pluggable transport bridge.
└── run-client.sh                   # A script for locally running the pluggable transport client.
.gitignore
mkdocs.yml                          # Config for the full documentation
readme.md                           # Basic readme to get started
requirements.txt                    # Python requirements for building the documentation using mkdocs
```
