import asyncio
import websockets
import os
import base64
import shutil
import subprocess
import sys

STYLE_TRANSFER_DIR = "samples/style_transfer"

async def process_style_transfer(websocket):
    try:
        # Clear and recreate the style transfer directory
        shutil.rmtree(STYLE_TRANSFER_DIR, ignore_errors=True)
        os.makedirs(STYLE_TRANSFER_DIR, exist_ok=True)
        
        # Receive input file
        input_data = b''
        while True:
            message = await websocket.recv()
            if message == "START_INPUT":
                continue
            if message == "END_INPUT":
                break
            input_data += base64.b64decode(message)
            
        with open(os.path.join(STYLE_TRANSFER_DIR, "input.wav"), 'wb') as f:
            f.write(input_data)
            
        # Receive generated file
        generated_data = b''
        while True:
            message = await websocket.recv()
            if message == "START_GENERATED":
                continue
            if message == "END_GENERATED":
                break
            generated_data += base64.b64decode(message)
            
        with open(os.path.join(STYLE_TRANSFER_DIR, "reference.wav"), 'wb') as f:
            f.write(generated_data)

        # Run style transfer
        cmd = [
            sys.executable,  # Use current Python interpreter
            "inference/style_transfer.py",
            "--ckpt_path_enc", "models/FXencoder_ps.pt",
            "--ckpt_path_conv", "models/MixFXcloner_ps.pt",
            "--target_dir", STYLE_TRANSFER_DIR
        ]

        try:
            print("\n=== Running style transfer ===")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Style transfer failed: {e.returncode}\n{e.stderr}")
            raise

        # Verify that the output file exists
        output_path = os.path.join(STYLE_TRANSFER_DIR, "mixture_output.wav")
        if not os.path.exists(output_path):
            raise RuntimeError("Style transfer output file not found")

        # Send the output file in chunks
        message = await websocket.recv()
        if message != "READY_FOR_OUTPUT":
            raise Exception("Unexpected message received: " + message)
        
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(os.path.join(STYLE_TRANSFER_DIR, "mixture_output.wav"), 'rb') as f:
            while chunk := f.read(chunk_size):
                await websocket.send(base64.b64encode(chunk).decode('utf-8'))
        
        await websocket.send("END_OUTPUT")

    except Exception as e:
        raise RuntimeError(f"Style transfer failed: {str(e)}")
    
async def main():
    async with websockets.serve(
        process_style_transfer, 
        "0.0.0.0", 
        8765,
        ping_interval=20, # Send ping every 20 seconds
        ping_timeout=300, # Wait up to 5 minutes for pong response
        max_size=1024 * 1024 * 1024  # 1GB
    ):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())