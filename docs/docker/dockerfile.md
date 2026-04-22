# dockerfile

This chapter explains the inner workings of the dockerfile. The specific example is that of the client's dockerfile, but that of the server is identical apart from directory names. Arch linux is used because pacman always ships the newest version of Tor per default. Under package managers like apt, this has to be configured first. This file should, however, be self-explanatory for anyone who has worked with dockerfiles in the past.

```yaml
FROM archlinux:latest

# Install tor
RUN pacman -Sy --noconfirm tor && pacman -Scc --noconfirm # Update packages

# Create non-root user for tor
RUN useradd -m toruser
USER toruser

WORKDIR /app

# Copy torrc + PT binary
COPY docker_deployment/client/torrc /app/torrc # Get the torrc into the container's filesystem
COPY --chown=toruser:toruser /shadow/lyrebird /usr/local/bin/lyrebird # Get lyrebird into the container's filesystem

# Entrypoint handles the Tor invocation
COPY docker_deployment/client/entrypoint.sh /entrypoint.sh # Copy a script that serves as the entrypoint for the container. The script sets up permissions and runs Tor as non-root
ENTRYPOINT ["/entrypoint.sh"]
```
