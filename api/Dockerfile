FROM python:3.9.20

WORKDIR /workspace

RUN pip install \
    librosa==0.10.2.post1 \
    python-multipart==0.0.17 \
    huggingface_hub==0.26.2 \
    hf_transfer==0.1.8 \
    torch==2.5.1 \
    soundfile==0.12.1 \
    diffusers==0.31.0 \
    transformers==4.46.2 \
    accelerate==1.1.1 \
    torchsde==0.2.6 \
    fastapi==0.115.4 \
    uvicorn==0.32.0 \
    websockets==14.1

CMD ["/bin/bash"]