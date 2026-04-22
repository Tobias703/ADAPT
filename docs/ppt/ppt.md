# Python Pluggable Transport (PPT)

This section talks about the Python Pluggable Transport: A framework for (hopefully) easily and quickly developting simple Pluggable Transports. The codebase is meant to be as clean as possible to help anyone who wants to implement a Pluggable Transport in another programming language to understand and reproduce the logic that makes a PT work.

## What can and can't PPT do?

This framework is mainly meant to educate on pluggable transports, so that developters can rapidly implement simple transports or cross-reference the inner workings of the framework, to create their own codebase, possibly in another language. In order to cleanly implement the framework into the intended ecosystem, a few assumptions were made

### Assumption 1 - PPT will be used with the current version of Tor

As mentioned in the [general information](../general/general.md), Tor uses the [Pluggable Transport Specification V1.0](https://github.com/Pluggable-Transports/Pluggable-Transports-spec/blob/main/releases/PTSpecV1.0/pt-1_0.txt). This is why PPT is tested to work with PT-Spec V1.0 specifically. There **IS** logic to use PPT with even the newest PT-Spec (V3.0); this has however never been tested in production and it cannot be said for certain if this would work without issues as this was not the primary design goal.

### Assumption 2 - PPT is not used in a security-critical scenario

Tor has an intended trust boundary between a PT binary and the Tor process. The PT-binary usually authenticates itself and sends per-connection metadata via the Extended Onion Routing Prot (ExtORPort). PPT does not use the ExtORPort currently. This means, abuse detection/ratelimiting won't work and any arbitrary process can inject raw TCP packets into the ORPort and Tor will treat it as packets from the PT binary (since it is, as already mentioned, not authenticated).

!!! Danger
    Never use PPT in any sort of security critical application

### Assumption 3 - Users only want to do some 'bit juggeling'

PPT does only provide three properties in creating a new PT. The first is the name, which has nothing to do with the PT's logic, the second and third are the en- and decryption functions. These are rather basic. The user gets a datastream and can manipulate in any way they please. This does by default not provide any deep access to raw network packets. This is currently not available without touching the helper-scripts.

### Assumption 4 - There is no need to protect against active probing

PTs like obfs4 are authenticated specifically to prevent active probing by just not responding at all if the credentials are wrong. PPT does not implement support for authenticated PTs per default and as such does not protect against active probing.

## Getting started

The following sections will give instructions on how to get up and running with developing PTs using PPT.

### Prerequisites

PPT is, like this entire project, mainly written for linux. You can attempt to translate every used bash script to other platforms like Windows or macOS. This should work without issues but is untested.

As the name says, the Python Pluggable Transport uses Python. Python is actually the only requirement for PPT.

PPT and all of its components work completely without any external Python libraries (almost). The only external Python library that is technically needed is `pyinstaller`. This dependency however does not need to be installed or interacted with by the user at all, since the `build.sh` script in the `pythonPluggableTransport` directory takes care of managing the dependency all by itself, installing it in a Virtual Environment at the project root.

### How do you create a new Pluggable Transport within PPT?

Creating a new PT within PPT is meant to be as easy as possible. A simple pluggable transport with custom encryption is really just the name of the PT, and two functions to en- and decrypt the data. This is why PPT has reduced the entire PT-logic to just these three components. The following is a Template for implementing a simple new Pluggable Transport within PPT. To do this, PT name and en-/decryption functions have to be defined and the script has to be put into `./pythonPluggableTransport/transports` as a python script. Then, the `__init__.py` in the same directory has to be extended by importing the newly added python script. And that's all. The next time PPT is built, the new transport will become available. The template looks as simple as this:

```python
import logging
from typing import Tuple
from helpers.transport import BaseTransport, register

log = logging.getLogger(__name__)

@register
class InvertTransport(BaseTransport):
    name = "<transport_name>"

    def encode(self, data: bytes) -> bytes:
        <encryption logic>

    def decode(self, buf: bytes) -> Tuple[bytes, bytes]:
        <decryption logic>
```

#### Sanity testing the Transport

Since implementing a transport, compiling it's binary, running it through Tor and checking if the connection works is wayy to complex just so you can verify if the current implementation is working or not. For faster testing during development, the `test_pt.py`-script can be used. This script is very straightforward to use since it neither requires the python project to be compiled into a binary nor does it need any external libraries. To run the script, simple use `python3 ./test_pt.py -t <transport>` to test the transport with the name `<transport>`. This will automatically run over 30 tests, including data roundtrips with any possible byte, empty data and even integrity checks like emmitting of version lines, clean exits on sigterm and many many more. At the time of writing, running the tests takes about 2.5 seconds if every test is successful. If tests are failing, execution might take up to 20 seconds. This is still a lot faster then building the binary and testing in shadow.

#### Deploying the Transport

Now that the new transport is defined and passing the tests, it can be deployed by whichever deployment method is preferred. For this, simply execute the `build.sh` script. This should take a few seconds and generate a binary called `ppt` in the `./dist/` directory within the PPT directory. This binary should now be a fully functional Pluggable Transport binary that works in the live Tor network as well as under Shadow. For further deployment instructions, refer to [Running a PT](../general/running-a-pt.md) or take a look at any of the deployment methods ([Shadow deployment](../shadow/getting-started.md), [local deployment](../local/local.md) or [Docker deployment](../docker/docker.md))
