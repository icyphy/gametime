# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.2/containers/python-3-anaconda/.devcontainer/base.Dockerfile

FROM mcr.microsoft.com/vscode/devcontainers/anaconda:0-3

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Copy environment.yml (if found) to a temp location so we update the environment. Also
# copy "noop.txt" so the COPY instruction does not fail if no environment.yml exists.
COPY conda_environment.yml .devcontainer/noop.txt /tmp/conda-tmp/
RUN if [ -f "/tmp/conda-tmp/conda_environment.yml" ]; then umask 0002 && /opt/conda/bin/conda env update -n base -f /tmp/conda-tmp/conda_environment.yml; fi \
    && rm -rf /tmp/conda-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends clang-format \
#     clang-tidy clang-tools clang clangd libc++-dev libc++1 libc++abi-dev libc++abi1 \ 
#     libclang-dev libclang1 liblldb-dev libllvm-ocaml-dev libomp-dev \ 
#     libomp5 lld lldb llvm-dev llvm-runtime llvm python3-clang 

# # FROM debian:bullseye 
# Note: Microsoft uses debian:bullseye in the first place. 

# Install dependencies
RUN apt-get -qq update; \
    apt-get install -qqy --no-install-recommends \
        gnupg2 wget ca-certificates \
        autoconf automake cmake dpkg-dev file make patch libc6-dev

# Set repository key
RUN wget -nv -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -

# Install
RUN echo "deb http://apt.llvm.org/bullseye/ llvm-toolchain-bullseye main" \
        > /etc/apt/sources.list.d/llvm.list; \
    apt-get -qq update && \
    apt-get install -qqy -t llvm-toolchain-bullseye \
        clang clang-tidy clang-format lld llvm && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN apt-get -qq update && \
    apt-get install -qqy --no-install-recommends \
        ca-certificates \
        autoconf automake cmake dpkg-dev file git make patch \
        libc-dev libc++-dev libgcc-10-dev libstdc++-10-dev  \
        dirmngr gnupg2 lbzip2 wget xz-utils libtinfo5 && \
    rm -rf /var/lib/apt/lists/*

# Signing keys
ENV GPG_KEYS 09C4E7007CB2EFFB A2C794A986419D8A B4468DF4E95C63DC D23DD2C20DD88BA2 8F0871F202119294 0FC3042E345AD05D

# Retrieve keys
RUN gpg --batch --keyserver keyserver.ubuntu.com --recv-keys $GPG_KEYS

# Version info
ENV LLVM_RELEASE 14
ENV LLVM_VERSION 14.0.0

# Install Clang and LLVM
COPY docker/install.Unix.sh .
RUN ./install.Unix.sh
