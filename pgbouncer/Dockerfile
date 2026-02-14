FROM debian:bookworm-slim

# Install PgBouncer from apt.postgresql.org (PGDG) to stay close to latest stable.
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates wget gnupg \
  && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
  wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /usr/share/keyrings/postgresql.gpg; \
  echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends pgbouncer; \
  rm -rf /var/lib/apt/lists/*

RUN useradd --system --home /nonexistent --shell /usr/sbin/nologin pgbouncer

EXPOSE 6432

CMD ["pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]
