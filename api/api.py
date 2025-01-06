from diffusers import StableAudioPipeline
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import torch
import soundfile as sf
import tempfile
import shutil
import zipfile
import uvicorn
import librosa
import logging
import websockets
import base64

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CUDA
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Load model globally
pipe = StableAudioPipeline.from_pretrained("model/stabilityai/stable-audio-open-1.0", torch_dtype=torch.float16)
pipe = pipe.to("cuda")

async def style_transfer_websocket(input_path: str, generated_path: str, output_path: str):
    try:
        # Increased timeout for the connection
        async with websockets.connect(
            'ws://style-transfer:8765',
            ping_interval=20, # Send ping every 20 seconds
            ping_timeout=300, # Wait up to 5 minutes for pong response
            max_size=1024 * 1024 * 1024  # 1GB
        ) as websocket:
            # Send input file
            await websocket.send("START_INPUT")
            with open(input_path, 'rb') as f:
                while chunk := f.read(1024 * 1024):  # 1MB chunks
                    try:
                        await websocket.send(base64.b64encode(chunk).decode('utf-8'))
                    except Exception as e:
                        logger.error(f"Error sending input file: {str(e)}")
                        raise
            await websocket.send("END_INPUT")
            
            # Send generated file
            await websocket.send("START_GENERATED")
            with open(generated_path, 'rb') as f:
                while chunk := f.read(1024 * 1024):
                    try:
                        await websocket.send(base64.b64encode(chunk).decode('utf-8'))
                    except Exception as e:
                        logger.error(f"Error sending generated file: {str(e)}")
                        raise
            await websocket.send("END_GENERATED")
            
            # Receive the processed file
            output_data = b''
            await websocket.send("READY_FOR_OUTPUT")
            try:
                while True:
                    message = await websocket.recv()
                    if message == "END_OUTPUT":
                        break
                    output_data += base64.b64decode(message)
            except Exception as e:
                logger.error(f"Error receiving output file: {str(e)}")
                raise
                
            with open(output_path, 'wb') as f:
                f.write(output_data)
                
    except Exception as e:
        raise RuntimeError(f"Style transfer failed: {str(e)}")

@app.post("/process-audio")
async def process_audio(
    background_tasks: BackgroundTasks, 
    audio_file: UploadFile = File(...),
    user_prompt: str = Form(default="")
):
    try:
        logger.info(f"User prompt: {user_prompt}")

        # Clear GPU memory before generation
        torch.cuda.empty_cache()
        logger.info("GPU memory cleared before generation")

        # Create temporary directory with unique name
        temp_dir = tempfile.mkdtemp(prefix="audio_")
        input_path = f"{temp_dir}/input.wav"
        output_path = f"{temp_dir}/processed_audio.zip"
        
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Calculate duration of input audio
        audio_data, sr = librosa.load(input_path)
        duration = librosa.get_duration(y=audio_data, sr=sr)
        
        generator = torch.Generator("cuda").manual_seed(0)

        logger.info("Generating audio...")

        audio = pipe(
            user_prompt,
            negative_prompt="Low quality.",
            num_inference_steps=200,
            audio_end_in_s=duration,
            num_waveforms_per_prompt=3,
            generator=generator,
        ).audios

        logger.info("Audio generation completed")

        # Clear GPU memory
        torch.cuda.empty_cache()
        logger.info("GPU memory cleared")
        
        with zipfile.ZipFile(output_path, 'w') as zip_file:
            for i, audio_sample in enumerate(audio):
                # Save the generated audio
                output = audio_sample.T.float().cpu().numpy()
                generated_path = f"{temp_dir}/audio_{i+1}_generated.wav"
                sf.write(generated_path, output, pipe.vae.sampling_rate)
                
                # Apply style transfer
                style_transferred_path = f"{temp_dir}/audio_{i+1}_style_transferred.wav"
                logger.info(f"Applying style transfer to audio {i+1}")
                await style_transfer_websocket(input_path, generated_path, style_transferred_path)
                
                # Add style-transferred version to ZIP file
                zip_file.write(style_transferred_path, f"audio_{i+1}_style_transferred.wav")

        # Add cleanup task
        def cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        background_tasks.add_task(cleanup)

        # Return the ZIP file
        return FileResponse(
            output_path,
            media_type="application/zip",
            filename="processed_audio.zip"
        )

    except Exception as e:
        logger.error(f"Error during audio processing: {str(e)}", exc_info=True)
        # Clean up if there's an error
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Clear GPU memory even if there's an error
        torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)