FROM registry.access.redhat.com/ubi9/ubi:9.8 AS builder

RUN dnf update -y && \
    dnf install -y make gcc openssl-devel && \
    adduser ircd;

USER ircd

RUN cd /home/ircd && \
    curl -sOL https://www.unrealircd.org/downloads/unrealircd-latest.tar.gz && \
    tar xzf unrealircd-latest.tar.gz && \
    cd $(find ./ -type d -iname "unrealircd-6*" | sort -r | head -n 1) && \
    printf "\n\n\n\n\n\n\nNo\n\n\n\n\n\n\n\n\n\n\n\n\n\n" | ./Config && \
    make -j 8 && \
    make install;

FROM registry.access.redhat.com/ubi9/ubi:9.8

RUN dnf update -y && \
    adduser ircd;


USER ircd
COPY --chown=1000:1000 --from=builder /home/ircd/unrealircd /home/ircd/unrealircd

RUN rm -f /home/ircd/unrealircd/source
VOLUME ["/home/ircd/unrealircd/conf/unrealircd.conf"]
WORKDIR /home/ircd/unrealircd

CMD ["/home/ircd/unrealircd/bin/unrealircd"]
