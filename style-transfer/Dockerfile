FROM python:3.9.20

WORKDIR /workspace

RUN pip install numpy==1.23.0 typing_extensions==4.12.2 && \
    pip install \
    aubio==0.4.9 \
    classy_vision==0.6.0 \
    config==0.5.1 \
    librosa==0.9.2 \
    matplotlib==3.3.3 \
    numba==0.53.0 \
    psutil==5.7.2 \
    pyloudnorm==0.1.0 \
    git+https://github.com/csteinmetz1/pymixconsole \
    pytorch-lightning==1.5.10 \
    PyYAML==5.4 \
    scikit_learn==1.1.3 \
    scipy==1.6 \
    soundfile==0.12.0 \
    soxbindings==1.2.3 \
    torch==1.13.0 \
    torchaudio==0.13.0 \
    torchvision==0.14.0 \
    torchtext==0.14.0 \
    torchmetrics==0.6.0 \
    demucs==4.0.1 \
    websockets==14.1

RUN apt-get update && apt-get install -y sox

CMD ["/bin/bash"]
