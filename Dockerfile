FROM python:3-slim
WORKDIR /opt/warp

# Create warp user and group with specific UID/GID
RUN groupadd -g 1002 warp && \
    useradd -u 1002 -g warp -s /bin/false -M warp

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 mime-support libpcre3 curl sqlite3 && \
    rm  -rf /var/lib/apt/lists/*

RUN \
    --mount=type=bind,from=compile-image,source=/opt/warp/wheel,target=./wheel \
    pip install --no-index wheel/*.whl

COPY --from=compile-image /opt/warp/warp/static ./static
COPY res/warp_uwsgi.ini .

# Create necessary directories with proper permissions
RUN mkdir -p /opt/warp/data /opt/warp/sql && \
    chown -R warp:warp /opt/warp && \
    chmod -R 755 /opt/warp

COPY warp/sql/sqlite_schema.sql /opt/warp/sql/

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh && \
    chown warp:warp /docker-entrypoint.sh

# Switch to non-root user
USER warp

EXPOSE 8000/tcp

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "warp_uwsgi.ini"]