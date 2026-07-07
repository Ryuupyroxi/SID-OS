# SID OS Build Container
FROM alpine:3.24 AS builder

LABEL description="SID OS Build Environment"
LABEL version="1.0.0"

RUN apk add --no-cache \
    build-base linux-headers ncurses-dev python3 py3-pip \
    cmake git wget curl xorriso syslinux squashfs-tools \
    cpio gzip busybox

WORKDIR /build
COPY scripts/build-sid.sh .
RUN chmod +x build-sid.sh

# Build phase
RUN ./build-sid.sh

# Final minimal image with SID
FROM scratch
COPY --from=builder /output/ /
CMD ["/bin/sh"]
