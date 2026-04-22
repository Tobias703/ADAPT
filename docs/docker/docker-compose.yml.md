# docker-compose.yml

This page will show the docker-compose.yml and explain the most important options within the configuration. A basic understanding of docker compose will be assumed. Only Tor/PT specific quirks will be explained.

```yaml
services:
  pt-bridge:
    build: 
      context: ../
      dockerfile: docker_deployment/bridge/Dockerfile
    container_name: pt-bridge
    networks:
      tornet:
        ipv4_address: 172.21.0.10 # This has to be defined, since a torrc CANNOT resolve hostnames. With additional setup, this could be skipped if the hostnames of the containers would be resolved and inserted into the torrc at container startup. This is left out of this implementation for simplicity.

  pt-client:
    build:
      context: ../
      dockerfile: docker_deployment/client/Dockerfile
    container_name: pt-client
    networks:
      tornet:
        ipv4_address: 172.21.0.11 # Same as above, the IP needs to be static and known for the torrcs
    ports:
      - "9052:9052" # The SOCKS5 port for connecting to the PT client has to be exposed. The rest is docker-internal

networks:
  tornet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/24 # The bridge network has to have its predefined IP range for the custom IP designations to work
```
