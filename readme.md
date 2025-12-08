# Tor Pluggable Transport in Rust
This is a project that implements a Tor pluggable transport in Rust, including pt-client as well as pt-server. The project's convenience script's are built for Linux.

## Getting Started
This section will guide you through setting up and running the pluggable transport.

### Prerequisits
To run this project you will need at least one of two things:
- Either you will need to have `tor` as well as `rustup` installed on your system, to run the pluggable transport locally
- Or you will need to have `docker` as well as `docker compose` installed, to runn the pluggable transport in a containerized environment

### Running the pluggable transport
To run the pluggable transport locally, you can use the `run-client.sh` and `run-server.sh` scripts in `./scripts` respectively

To run the pluggable transport under docker, use the `build-and-run-container.sh` script in `./scripts` to first build the containers. After that, you can also run `docker compose up -d` from within `./docker` to start the containers. Within this folder, you can also use `docker compose down` to stop the containers. To access the container logs, you can use the `docker-client-logs.sh` as well as the `docker-server-logs.sh` scripts in `./scripts`.

## Known Issues and Troubleshooting
- Tor Client get's stuck at 25% Bootstrapped: 
    - The tor-network isn't having a good day. In most cases this can be fixed by just waiting. Sometimes, this is a looong wait (I've never seen it longer than an hour though).