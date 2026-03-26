# Getting started with Shadow

This project currently supports two different ways of using Shadow. If you are running on a supported version of linux (which can be found here: <https://shadow.github.io/docs/guide/supported_platforms.html>), you can install Shadow on your local machine and run the simulation on your host system. If you are on an unsupported platform or you don't want to install Shadow locally, this project also supports a Docker Container for running shadow. Instructions for setting up these two types of deployment can be found below.

## Local installation

The first step for using shadow is installing shadow, as well as it's dependencies. The following guide is written for Ubuntu, using `apt` as the package manager. The same concepts should also be applicable to any other distributions. The documentation also provides instructions for installing shadow on systems using `dnf` as the package manager.

### Dependencies

The dependencies for shadow can be found here: <https://shadow.github.io/docs/guide/install_dependencies.html>

Additional dependencies you might want to install are:

- **git** for cloning the repository
- **curl** for installing rustup
- **tor** which is used in the simulation. Installing Tor via `apt` usually does not yield the newest version. This is fine for shadow but might cause issues with an actual deployment. To get the newest version of Tor, refer to this site: <https://support.torproject.org/little-t-tor/getting-started/installing/>

To give the shadow-setup in the next step a better chance of succeeding, reboot your PC after installing the dependencies.

### Installation

Now that the dependencies are installed the next step is to clone the git repository, build shadow and then install it. The full installation instructions can be found here: <https://shadow.github.io/docs/guide/install_shadow.html>

Additional notes:

- It is normal for a few tests (~5) to fail when running shadow's tests.
- This project expects you to add shadow to your `PATH`, as is described in the installation instructions.
- Once you are done installing shadow, you can test if your implementation is working by running the `run_shadow.sh` script within this project's `shadow` directory. If the simulation finishes without errors, you can assume shadow works.

## Docker deployment

For a Docker deployment, the user only has to have `Docker` and `Docker compose` installed. In the following, there will be explanations and quirks for each common type of operating system on how to get the Docker deployment to work and what to look out for. It is still strongly recommended to use Linux as some simple testing has shown that running the simulation on Linux took about 14 seconds while running it on the same hardware but on windwos took over a minute.

!!! note
    Independent of your operating system, the first launch of the container will take a very long time. This is due to the fact, that the container has to be built first. Running the container subsequent times, execution will be much quicker since docker stores the built image and only needs to run Shadow in the already built container.

### Linux

Linux deployment is simple. You need to install `docker` and `docker compose` and simply run the `docker_run.sh` script inside the `shadow` directory. This will automatically set up a configuration to run the container with your user and then execute the container.

You could also do a simple `docker compose up`, this will however not provide your user and thus make the output of your simulation owned by root which will make problems when trying to read/modify/delete the output. The script is the easiest and recommended way to execute the container.

### Windows

On windows, you only have to install `Docker Desktop` (online or via the MS Store). You can then navigate into the `shadow` directory in the terminal and run the command `docker compose up`.

#### Known issues

|Output|Explanation/Fix|
|-|-|
|`**time="2026-03-26T14:37:56+01:00" level=warning msg="The \"UID\" variable is not set. Defaulting to a blank string."`|This is perfectly normal. This variable is only needed for permission management in Linux. Windows does not need that.|
|`/workspace/shadow_run.sh: line 2: cd: $'/workspace\r': No such file or directory`|The issue here are windows lineendings. Open the `shadow_run.sh` script in the `shadow` directory in VSCode, and on the lower right corner of the screen, press on `CRLF` and select `LF` in the resulting menu|

### macOS

There are currently no instructions for running the Shadow container on macOS. Feel free to try such a deployment and add your experiences to this documentation!
