# ADAPT - Accelerated Development & Adaption of Pluggable Transports

This Project is supposed to teach about the internals of Tor Pluggable Transports to get you started with developing your own Pluggable Transport as quickly as possible.

This readme contains the basic structure and the features of this project. For more details on getting started with each component of the project and additionall background information visit the full documentation at <https://tobias703.github.io/ADAPT/> or build it via MKDocs locally.

## Supported platforms

ADAPT is mainly built for linux. The distribution should not matter, however there might be issues with Arch shipping software versions that are "too recent" for some of the used code (Shadow and its dependencies), which resulted in a need for manual patching.

To circumvent a hard limit on Operating System this project offers a containerised alternative to anything that does not "just use Python". As such, the entire project should work on any Operating System that has both Python and Docker Compose installed. As already stated though, the project is built with mainly linux in mind and as such most convenience scripts may have to be translated into different OS ecosystems first. On Windows, WSL2 is also a great way of running the project.

## What does this Project offer?

This project is meant to make Tor Pluggable Transports more accessible and make learning about them easier. For this purpose, the technologies in this project can be split into three major categories. Each of the categories, as well as a description of its implemented components will be listed in the following.

### Pluggable Transport Deployment Examples

Both the docker_deployment and local_deployment components of this project fall under this category. The main point is to show how Tor has to be configured to successfully run a Pluggable Transport. These deployments are built to run purely locally, which does defeat the point of having a Pluggable Transport. This is done for demonstration purposes. Reconfiguring these deployments for actual live deployment should be very straightforward.

### Pluggable Transport Implementation Framework

The pythonPluggableTransport in this Project is a simple Framework to implement very basic Pluggable Transports in as few as around 13 lines of code! This framework does not yet provide deep reaching packet manipulation or authentication via the ExtORPort (more on that in the full documentation), but it can help get an understanding on how Pluggable Transports work. The codebase is also kept as clean as possible so that it can be referenced if one wants to build a Pluggable Transport from the ground up or in another programming language.

### Tor Network Simulation using Shadow

Shadow is a simulation platform to simulate a realistic and deterministic Tor network. In order to test or demonstrate Pluggable Transports this platform can be used to avoid the flaky nature of the Tor network becuase Pluggable Transports can sometimes take very long to Bootstrap into the real network. This is complete with virtual hosts talking to each other in a simulated network. Users get access to the full output logs of these Hosts aswell as pcap files of the Host's network flows to inspect in wireshark. The simulation executes very quickly under Linux but can take up to a minute or two on other operating systems on the same hardware if ran using the docker deployment.

## Quick collection of useful links

If you are just interrested in some Resources regarding Tor Pluggable Transports, here's a collection of useful resources and a short description for each of them:

As mentioned, the full documentation of this project should teach you all the basics: <https://tobias703.github.io/ADAPT/>

If you want the current specification for Pluggable Transports, here's the link to that. Please note that Tor is using the PT-Specification V1.0 so if you want to use Tor, refer to that instead of the newest version which, at the time of writing, is V3.0: <https://github.com/Pluggable-Transports/Pluggable-Transports-spec/tree/main>

To find out how to install THE NEWEST VERSION of Tor in order to avoid deployment issues, refer to this guide: <https://support.torproject.org/little-t-tor/getting-started/installing/>

Since the specification for the Tor configuration (i.e. torrc files) is very hard to find, I'll link it here: <https://2019.www.torproject.org/docs/tor-manual.html.en>

The code for the Shadow Network Simulator can be found here: <https://github.com/shadow/shadow>

The documentation for Shadow is here: <https://shadow.github.io/docs/guide/shadow.html>
