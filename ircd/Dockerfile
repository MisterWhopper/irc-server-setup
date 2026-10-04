FROM registry.access.redhat.com/ubi9/ubi:9.8 AS builder

RUN dnf update -y && \
    dnf install -y cmake make gcc g++ openssl-devel && \
    adduser ircd;

USER ircd

RUN cd /home/ircd && \
    curl -sOL https://www.unrealircd.org/downloads/unrealircd-latest.tar.gz && \
    tar xzf unrealircd-latest.tar.gz && \
    cd $(find ./ -type d -iname "unrealircd-6*" | sort -r | head -n 1) && \
    printf "\n\n\n\n\n\n\nNo\n\n\n\n\n\n\n\n\n\n\n\n\n\n" | ./Config && \
    make -j 8 && \
    make install;

# Not using this bc it's older than dirt (unless I later determine it's required for some reason)
#RUN cd /home/ircd && \
#    curl -sL https://github.com/anope/anope/archive/refs/tags/2.0.20.tar.gz -o anope-2.0.20.tar.gz && \
#    tar xzf anope-2.0.20.tar.gz && \
#    cd anope-2.0.20 && \
#    printf "/home/ircd/svc\n\n\n\n\n\nNONE\nNONE\nNONE\n" | ./Config && \
#    cd build && \
#    make -j 8 && \
#    make install;

FROM registry.access.redhat.com/ubi9/ubi:9.8

RUN dnf update -y && \
# In case supervisord is ever needed
#     dnf install -y python3-pip && \ 
    adduser ircd;


USER ircd
COPY --chown=1000:1000 --from=builder /home/ircd/unrealircd /home/ircd/unrealircd
# COPY --chown=1000:1000 --from=builder /home/ircd/svc /home/ircd/svc

RUN rm -f /home/ircd/unrealircd/source
VOLUME ["/home/ircd/unrealircd/conf/unrealircd.conf"]
WORKDIR /home/ircd/unrealircd

CMD ["/home/ircd/unrealircd/bin/unrealircd"]
