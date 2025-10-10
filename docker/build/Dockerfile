FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHON=python3

# Refresh apt mirrors and install dependencies
RUN sed -i 's|http://archive.ubuntu.com|http://azure.archive.ubuntu.com|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com|http://azure.archive.ubuntu.com|g' /etc/apt/sources.list && \
    apt-get clean && apt-get update -o Acquire::CompressionTypes::Order::=gz && \
    apt-get install -y --no-install-recommends \
        git \
        uuid-dev \
        pkg-config \
        build-essential \
        wget \
        unzip \
        cmake \
        python3 \
        python3-distutils \
        python3-apt \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    $PYTHON get-pip.py && \
    rm get-pip.py

# Clone and install
ARG CACHE_DATE=not_a_date
RUN git clone https://github.com/SamueleGerminiani/llmAgent.git /llmAgent
WORKDIR /llmAgent

RUN bash install_deps.sh || true

CMD ["bash"]

