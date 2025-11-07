import pyaudio
import wave
import threading
import os
from datetime import datetime

class AudioRecorderHandler:
    def __init__(self, output_dir="recordings", sample_rate=16000, channels=1, chunk=1024):
        """
        Initialize the audio recorder
        
        Args:
            output_dir: Directory to save recordings
            sample_rate: Audio sample rate (16000 Hz for Whisper)
            channels: Number of audio channels (1 for mono)
            chunk: Audio chunk size
        """
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.format = pyaudio.paInt16
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Recording state
        self._recording = False
        self._frames = []
        self._thread = None
        self._audio = None
        self._stream = None
        
    def is_recording(self):
        """Check if currently recording"""
        return self._recording
    
    def _record_audio(self):
        """Internal method to record audio in a separate thread"""
        self._audio = pyaudio.PyAudio()
        
        try:
            # Open audio stream
            self._stream = self._audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print(" Recording started...")
            self._frames = []
            
            # Record until stopped
            while self._recording:
                try:
                    data = self._stream.read(self.chunk, exception_on_overflow=False)
                    self._frames.append(data)
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    break
                    
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self._recording = False
        finally:
            # Clean up stream
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if self._audio:
                self._audio.terminate()
    
    def start_recording(self):
        """Start recording audio"""
        if self._recording:
            print(" Already recording!")
            return False
        
        self._recording = True
        self._thread = threading.Thread(target=self._record_audio, daemon=True)
        self._thread.start()
        return True
    
    def stop_recording(self):
        """Stop recording and save the audio file"""
        if not self._recording:
            print(" Not currently recording!")
            return None
        
        print(" Stopping recording...")
        self._recording = False
        
        # Wait for recording thread to finish
        if self._thread:
            self._thread.join(timeout=2.0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save the recording
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self._frames))
            
            print(f"💾 Recording saved: {filepath}")
            return filepath,True
            
        except Exception as e:
            print(f" Error saving recording: {e}")
            return None,False