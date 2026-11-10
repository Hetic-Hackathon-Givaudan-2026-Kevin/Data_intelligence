# Même base que l'image de production : Node 24 sur Debian trixie
FROM mcr.microsoft.com/devcontainers/typescript-node:24-trixie

# Utiliser plutôt un miroir français pour les paquets ubuntu (car, le dépôt officiel bloque HETIC)
RUN sed -i 's|deb.debian.org|ftp.fr.debian.org|g' /etc/apt/sources.list.d/debian.sources

# Client PostgreSQL (psql 17, comme le serveur)
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*