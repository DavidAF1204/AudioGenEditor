# AudioGen Editor
An interactive audio editing software that combines audio generation and style transfer.  
It allows users to selectively modify regions of audio tracks using text prompts and AI models.

## Features
- Upload and visualize WAV audio waveforms
- Select specific regions of audio for modification
- Generate audio variations based on text prompts
- Apply style transfer to maintain consistency with original audio
- Preview and choose from multiple generated variations
- Download the modified audio track

## Prerequisites
- NVIDIA GPU with CUDA support
- Docker and Docker Compose
- Internet connection for model downloads

## Setup Guide
1. Clone the repository:
```bash
git clone https://github.com/DavidAF1204/AudioGenEditor.git
cd AudioGenEditor
```

2. Download and extract the style transfer models:
```bash
cd style-transfer
# Download link: https://mycuhk-my.sharepoint.com/:u:/g/personal/1155174302_link_cuhk_edu_hk/EbngcBuwUMtHpFanrrqtsU8B0j3E11PVyw96mCTv41M-vw?e=F4cdvP
tar -xjf models.tar.bz2
cd ..
```

3. Make the setup script executable and run it:
```bash
chmod +x run-services.sh
./run-services.sh
```

The script will:
- Install necessary system dependencies:
  - tmux (terminal multiplexer for managing multiple terminal sessions)
  - npm (Node.js package manager)
  - http-server (lightweight web server for serving frontend files)
- Kill any processes using ports 8000 and 3000
- Stop and remove existing Docker containers
- Set up Docker containers:
  - API container (running FastAPI service)
  - Style Transfer container (running WebSocket service)
- Download Stable Audio Open 1.0 model from Hugging Face (if not already downloaded)
- Start the frontend server on port 3000
- Launch API server on port 8000
- Initialize WebSocket connection for style transfer service

4. Access the application at: `http://localhost:3000`

## Architecture
The system consists of three main components:

1. **Frontend** (Port 3000)
   - Web-based interface
   - Audio visualization and interaction
   - Region selection and playback controls

2. **API Server** (Port 8000)
   - Handles audio processing requests
   - Runs Stable Audio Open 1.0 model
   - Manages audio generation pipeline

3. **Style Transfer Service**
   - Processes audio style transfer
   - Maintains audio consistency
   - Communicates via WebSocket

Frontend <---> |RESTful API| API Server <---> |WebSocket| Style Transfer Service

## AI Models Used
1. **Stable Audio Open 1.0**
   - Purpose: Audio generation
   - Maximum audio length: 47 seconds
   - Input: Text prompt
   - Output: Multiple variations of audio matching the prompt
   - Runs on: API container with CUDA GPU
   - Model source: Hugging Face (stabilityai/stable-audio-open-1.0)

2. **Music Mixing Style Transfer**
   - Purpose: Audio style transfer
   - Input: Original audio segment and generated audio
   - Output: Style-transferred audio combining characteristics of both inputs
   - Runs on: Style Transfer container
   - Model source: Pre-trained models from music_mixing_style_transfer project

## Citations
[1] Z. Evans, J. D. Parker, C. J. Carr, Z. Zukowski, J. Taylor, and J. Pons, "Stable Audio Open," arXiv:2407.14358, 2024.

[2] StabilityAI, "stable-audio-open-1.0," Hugging Face. [Online]. Available: https://huggingface.co/stabilityai/stable-audio-open-1.0

[3] J. Koo, M. A. Martinez-Ramirez, W. Liao, S. Uhlich, K. Lee, and Y. Mitsufuji, "Music Mixing Style Transfer: A Contrastive Learning Approach to Disentangle Audio Effects," arXiv:2211.02247, 2022.

[4] J. Koo, "music_mixing_style_transfer," GitHub. [Online]. Available: https://github.com/jhtonyKoo/music_mixing_style_transfer

## Screenshot of application
![AudioGen Editor Interface](https://i.imgur.com/r5NUNcV.png)