import WaveSurfer from 'https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.esm.js'
import RegionsPlugin from 'https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.esm.js'
import { WaveFile } from 'https://esm.sh/wavefile';

let waveSurfer;
let activeRegion = null;
let originalAudioBuffer = null;

// Initialize WaveSurfer with regions plugin
function initWaveSurfer() {
  waveSurfer = WaveSurfer.create({
    container: "#waveform",
    waveColor: "#ffce3a",
    progressColor: "#ff7e5f",
    cursorColor: "#fff",
    responsive: true,
    interact: true,
    plugins: [
      RegionsPlugin.create({
        dragSelection: {
          color: 'rgba(255, 0, 0, 0.1)',
        },
        slop: 5,
        drag: true,
        resize: true,
      }),
    ],
  });

  // Get the regions plugin instance
  const regionsPlugin = waveSurfer.plugins[0];

  // Enable drag selection when waveform is ready
  waveSurfer.on('ready', () => {
    regionsPlugin.enableDragSelection({
      color: 'rgba(255, 0, 0, 0.1)',
    });
  });

  // Region update events
  regionsPlugin.on('region-created', (region) => {
    if (activeRegion) {
      activeRegion.remove();
    }
    activeRegion = region;
    
    region.setOptions({
      drag: true,
      resize: true,
      color: `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.3)`
    });
  });

  // Track region updates
  regionsPlugin.on('region-update-end', (region) => {
    activeRegion = region;
  });

  // Store the original audio buffer when loaded
  waveSurfer.on('ready', async () => {
    const audioFile = document.getElementById("upload").files[0];
    const arrayBuffer = await audioFile.arrayBuffer();
    const audioContext = new AudioContext();
    originalAudioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  });
}

// Initialize on page load
initWaveSurfer();

// Handle file upload and waveform loading
document.getElementById("upload").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    const objectURL = URL.createObjectURL(file);
    waveSurfer.load(objectURL);
  }
});

// Handle playback controls
document.getElementById("play").addEventListener("click", () => waveSurfer.playPause());
document.getElementById("pause").addEventListener("click", () => waveSurfer.pause());
document.getElementById("back-to-start").addEventListener("click", () => waveSurfer.stop());

// Function to extract audio region
async function extractRegionAudio(audioBuffer, region) {
  const sampleRate = audioBuffer.sampleRate;
  const channels = audioBuffer.numberOfChannels;
  const startOffset = Math.floor(region.start * sampleRate);
  const endOffset = Math.floor(region.end * sampleRate);
  const length = endOffset - startOffset;

  const offlineContext = new OfflineAudioContext(channels, length, sampleRate);
  const source = offlineContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineContext.destination);
  source.start(0, region.start, region.end - region.start);

  return await offlineContext.startRendering();
}

function encodeWAV(audioBuffer) {
  const wav = new WaveFile();
  
  // Get all channels' data
  const channelsData = [];
  for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
    channelsData.push(audioBuffer.getChannelData(i));
  }
  
  wav.fromScratch(
    audioBuffer.numberOfChannels,
    audioBuffer.sampleRate,
    '32f',
    channelsData
  );

  wav.toBitDepth('16');

  return new Blob([wav.toBuffer()], { type: 'audio/wav' });
}

// Handle audio generation
document.getElementById("process").addEventListener("click", async () => {
  const audioFile = document.getElementById("upload").files[0];
  const userPrompt = document.getElementById("promptInput").value;

  if (!audioFile || !userPrompt || !activeRegion) {
    const missing = [];
    if (!audioFile) missing.push("audio file");
    if (!userPrompt) missing.push("prompt text");
    if (!activeRegion) missing.push("selected region");
    
    alert(`Please provide the following: ${missing.join(", ")}`);
    return;
  }

  try {
    // Extract the selected region
    const regionBuffer = await extractRegionAudio(originalAudioBuffer, activeRegion);
    const wavBlob = encodeWAV(regionBuffer);

    const formData = new FormData();
    formData.append("audio_file", new File([wavBlob], "region.wav"));
    formData.append("user_prompt", userPrompt);

    const response = await fetch("http://localhost:8000/process-audio", {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const zipBlob = await response.blob();
    const zip = await JSZip.loadAsync(zipBlob);

    const audioContainer = document.getElementById("audioPlayers");
    audioContainer.innerHTML = "";

    for (const [filename, file] of Object.entries(zip.files)) {
      if (!filename.endsWith(".wav")) continue;

      const audioBlob = await file.async("blob");
      const audioUrl = URL.createObjectURL(audioBlob);

      const playerContainer = document.createElement("div");
      playerContainer.className = "audio-player";

      const audio = document.createElement("audio");
      audio.controls = true;
      audio.src = audioUrl;

      const label = document.createElement("p");
      label.textContent = filename;

      const replaceButton = document.createElement("button");
      replaceButton.textContent = "Replace Region";
      replaceButton.onclick = async () => {
        try {
          const arrayBuffer = await audioBlob.arrayBuffer();
          const audioContext = new AudioContext();
          const newAudioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          
          // Create a new audio buffer with the same length as the original
          const fullLength = originalAudioBuffer.length;
          const newFullBuffer = audioContext.createBuffer(
            originalAudioBuffer.numberOfChannels,
            fullLength,
            originalAudioBuffer.sampleRate
          );
      
          // Copy the original audio data
          for (let channel = 0; channel < originalAudioBuffer.numberOfChannels; channel++) {
            const originalData = originalAudioBuffer.getChannelData(channel);
            const newData = newFullBuffer.getChannelData(channel);
            newData.set(originalData);
          }
      
          // Calculate start and end samples
          const startSample = Math.floor(activeRegion.start * originalAudioBuffer.sampleRate);
          const endSample = Math.floor(activeRegion.end * originalAudioBuffer.sampleRate);
      
          // Replace the region with new audio, handling different channel counts
          const channelsToReplace = Math.min(newFullBuffer.numberOfChannels, newAudioBuffer.numberOfChannels);
          for (let channel = 0; channel < channelsToReplace; channel++) {
            const newData = newFullBuffer.getChannelData(channel);
            const replacementData = newAudioBuffer.getChannelData(channel);
            for (let i = 0; i < (endSample - startSample); i++) {
              if (startSample + i < newData.length && i < replacementData.length) {
                newData[startSample + i] = replacementData[i];
              }
            }
          }
      
          // Update the waveform display
          const newBlob = encodeWAV(newFullBuffer);
          const newUrl = URL.createObjectURL(newBlob);
          waveSurfer.load(newUrl);
          originalAudioBuffer = newFullBuffer;

          const downloadButton = document.createElement('button');
          downloadButton.textContent = 'Download Audio';
          downloadButton.onclick = () => {
            const downloadLink = document.createElement('a');
            downloadLink.href = newUrl;
            downloadLink.download = 'modified_audio.wav';
            downloadLink.click();
          };

          // Remove existing download button if present
          const existingButton = document.querySelector('#download-button');
          if (existingButton) {
            existingButton.remove();
          }

          // Add ID and insert after waveform
          downloadButton.id = 'download-button';
          document.getElementById('waveform').after(downloadButton);
        } catch (error) {
          console.error("Error replacing region:", error);
          alert("Failed to replace region");
        }
      };

      playerContainer.appendChild(label);
      playerContainer.appendChild(audio);
      playerContainer.appendChild(replaceButton);
      audioContainer.appendChild(playerContainer);
    }
  } catch (error) {
    console.error("Error processing audio:", error);
    document.getElementById("error").textContent = "Failed to process audio.";
  }
});