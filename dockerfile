FROM archlinux:latest

# Update system + refresh keys
RUN pacman -Sy --noconfirm archlinux-keyring

# Full system upgrade
RUN pacman -Syu --noconfirm

# Install tor
RUN pacman -S --noconfirm tor

# Minimal cleanup
RUN pacman -Scc --noconfirm

# sleep
CMD ["sleep", "infinity"]