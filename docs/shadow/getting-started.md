# Getting started with Shadow

The first step for using shadow is installing shadow, as well as it's dependencies. The following guide is written for Ubuntu, using `apt` as the package manager. The same concepts should also be applicable to any other distributions. The documentation also provides instructions for installing shadow on systems using `dnf` as the package manager.

## Dependencies

The dependencies for shadow can be found here: [https://shadow.github.io/docs/guide/install_dependencies.html](https://shadow.github.io/docs/guide/install_dependencies.html)

Additional dependencies you might want to install are:

- **git** for cloning the repository
- **curl** for installing rustup
- **tor** which is used in the simulation. Installing Tor via `apt` usually does not yield the newest version. This is fine for shadow but might cause issues with an actual deployment. To get the newest version of Tor, refer to this site: [https://support.torproject.org/little-t-tor/getting-started/installing/](https://support.torproject.org/little-t-tor/getting-started/installing/)

To give the shadow-setup in the next step a better chance of succeeding, reboot your PC after installing the dependencies.

## Installation

Now that the dependencies are installed the next step is to clone the git repository, build shadow and then install it. The full installation instructions can be found here: [https://shadow.github.io/docs/guide/install_shadow.html](https://shadow.github.io/docs/guide/install_shadow.html)

Additional notes:

- It is normal for a few tests (~5) to fail when running shadow's tests.
- This project expects you to add shadow to your `PATH`, as is described in the installation instructions.
- Once you are done installing shadow, you can test if your implementation is working by running the `run_shadow.sh` script within this project's `shadow` directory. If the simulation finishes without errors, you can assume shadow works.
