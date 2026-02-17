# TORPEDO

This is the full documentation of TORPEDO - Tor Pluggable transport Engineering and Development Onboarding. It'll help you get started with developing Tor Pluggable Transports while trying to avoid as much Tor-Specific headaches as possible so you can focus on your Implementation and not be at the mercy of the Tor-Network having a good or bad day.

## Abbreviations
There are several terms and abbreviations used in this documentation. For clarity, they are listed here:

PT - Pluggable Transport

PT-client - The part of the PT, which is running on the user's machine

PT-bridge - In documentation also often referred to as 'PT-server', but for clarity in this project always referred to as 'PT-bridge' is the part of the PT, which is running on a server and acts as a bridge into the tor network.

## Where do I find what?

The documentation is split into several parts:

[The Basics](./basics/01-basics.md): This page talks about the theory behind Pluggable Transports and provides important foundational knowledge for implementing PTs.

[Local Hosting](./local/01-local.md): Here's all the Info about locally hosting and using PTs.

[Docker](./docker/01-docker.md): Here's everything regarding PTs hosted fully under docker. Note that hosting a client under docker and a bridge locally and vice versa is possible.

[Shadow](./shadow/01-shadow.md): This is the full documentation for the Shadow Network Simulator. It provides developers with a very quick, easy and most importantly deterministic way of testing their PTs without having to rely on the whims of the Tor-Network.

## Project layout
The following shows the Layout of the Project. Relevant files have small comments behind them to tell you what they roughly are. Important files will have their documentation pages linked.

    .github/
        workflows/
            ci.yml                      # CI-Config for deploying the documentation page.
    docker/
        bridge/
            dockerfile                  # Dockerfile for the Tor Pluggable Transport bridge under Docker.
            entrypoint.sh               # Entrypoint script, executed by the container when it starts.
            torrc                       # Tor config for the docker bridge.
        client/
            dockerfile                  # Dockerfile for the Tor Pluggable Transport client under Docker.
            entrypoint.sh               # Entrypoint script, executed by the container when it starts.
            torrc                       # Tor config for the docker client.
        docker-compose.yml              # Compose file for easily starting the containers.
        build-and-run-containers.sh     # A script for building and running the containers (run, if you canged a container's config or if you've never built them).
        run-containers.sh               # A script to run the containers. It also removes orphans in case there's some left over docker stuff floating around.
        bridge-logs.sh                  # Live view of the docker bridge's logs.
        client-logs.sh                  # Live view of the docker client's logs.
    docs/
        index.md                        # Full documentation title page.
        setup_docs.sh                   # Setup script for when you want to change and deploy the docs locally.
        [Further Documentation]
    shadow/
        conf/                           # A ton of shadow configuration. Taken directly from the examples in the Shadow Git repo.
            [...]                       
        shadow.data.template/           # Config for all the nodes in the Shadow network, many taken from the examples in the Shadow Git repo.
            [...]
        lyrebird                        # The executable for lyrebird, a pluggable transport implementing obfs3 and obfs4.
        run_shadow.sh                   # Convenience script for running the shadow simulation. Automatically clears the last simulation for a clean re-run.
        shadow.yaml                     # The main configuration for the Shadow simulator. Includes a description of each node and what they do.
        topology.gml                    # The Topology of the Shadow network. Defines which nodes exist and can talk to whom.
    src/
        bridge-torrc                    # Tor config for locally running the pluggable transport bridge.
        client-torrc                    # Tor config for locally running the pluggable transport client.
        run-bridge.sh                   # A script for locally running the pluggable transport bridge.
        run-client.sh                   # A script for locally running the pluggable transport client.
        main.rs                         # The main function for the code of a pluggable transport written in rust
    .gitignore
    Cargo.lock                          # For rust dependencies.
    Cargo.toml                          # Rust dependencies for the rust pluggable transport.
    mkdocs.yml                          # Config for the full documentation
    readme.md                           # Basic readme to get started
    requirements.txt                    # Python requirements for building the documentation using mkdocs