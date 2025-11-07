import torch
import os
import time
import librosa
import numpy as np
from transformers import (
    pipeline,
    WhisperForConditionalGeneration,
    WhisperProcessor,
    GenerationConfig,
)
from huggingface_hub import login

# Import the logging setup
from scripts.logSetup import setup_logging

# Initialize logger
logger = setup_logging()

class WhisperTranscriberHandler:
    def __init__(self):
        """Initialize and load the Whisper model"""
        logger.info("Initializing WhisperTranscriberHandler...")
        logger.info("Authenticating to Hugging Face...")
        
        try:
            # Authenticate to Hugging Face
            os.environ["HF_TOKEN"] = "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"
            login(token=os.environ["HF_TOKEN"])
            logger.debug("Hugging Face authentication successful")
            
        except Exception as e:
            logger.error("Failed to authenticate with Hugging Face: %s", str(e), exc_info=True)
            raise
        
        logger.info("Loading fine-tuned model and processor...")
        
        try:
            # Load Fine-tuned Model and Processor
            repo_path = "sankar-asthramedtech/finetuned_whisper-medium_on_pods_V-1.1"
            logger.debug("Loading model from repository: %s", repo_path)
            
            self.inference_model = WhisperForConditionalGeneration.from_pretrained(
                repo_path, token=os.environ["HF_TOKEN"]
            )
            logger.debug("Fine-tuned model loaded successfully")
            
            self.processor = WhisperProcessor.from_pretrained("openai/whisper-medium")
            logger.debug("Whisper processor loaded successfully")
            
            # Load base config from original Whisper
            base_config = GenerationConfig.from_pretrained("openai/whisper-medium")
            self.inference_model.generation_config = base_config
            logger.debug("Generation config loaded and applied")
            
        except Exception as e:
            logger.error("Failed to load model or processor: %s", str(e), exc_info=True)
            raise
        
        logger.info("Setting up pipeline...")
        
        try:
            # Define pipeline
            self.pipe = pipeline(
                task="automatic-speech-recognition",
                model=self.inference_model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                device_map="auto",
                return_timestamps=True,
                stride_length_s=15,
                generate_kwargs={
                    "language": "en",
                    "task": "transcribe",
                    "num_beams": 1,
                    "repetition_penalty": 1.0,
                    "length_penalty": 1.0,
                },
            )
            logger.debug("Pipeline configuration: stride_length_s=15, language=en, num_beams=1")
            logger.info("Whisper model loaded and ready!")
            
        except Exception as e:
            logger.error("Failed to create pipeline: %s", str(e), exc_info=True)
            raise
    
    def transcribe(self, audio_path):
        """
        Transcribe audio file using the loaded Whisper model
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcription text
        """
        logger.info("Starting transcription for audio file: %s", audio_path)
        
        # Validate audio file exists
        if not os.path.exists(audio_path):
            logger.error("Audio file not found: %s", audio_path)
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        file_size = os.path.getsize(audio_path)
        logger.debug("Audio file size: %.2f MB", file_size / (1024 * 1024))
        
        try:
            logger.debug("Loading audio with librosa (target sr=16000)...")
            # Load audio using librosa
            audio, sr = librosa.load(audio_path, sr=16000)  # Whisper expects 16kHz mono audio
            logger.debug("Audio loaded successfully. Sample rate: %d, Duration: %.2f seconds", 
                        sr, len(audio) / sr)
            
            # Ensure correct shape and type
            audio = np.array(audio)
            logger.debug("Audio array shape: %s, dtype: %s", audio.shape, audio.dtype)
            
        except Exception as e:
            logger.error("Failed to load audio file: %s", str(e), exc_info=True)
            raise
        
        try:
            logger.info("Running inference...")
            start_time = time.time()
            
            result = self.pipe(audio)
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            logger.info("Inference completed in %.2f seconds", inference_time)
            
            # Log transcription details
            transcription_text = result["text"]
            logger.debug("Transcription length: %d characters", len(transcription_text))
            logger.debug("Transcription preview: %s...", transcription_text[:100] if len(transcription_text) > 100 else transcription_text)
            
            # Log timestamps if available
            if "chunks" in result:
                logger.debug("Number of timestamp chunks: %d", len(result["chunks"]))
            if transcription_text != None:
                return transcription_text,True
            else:
                return transcription_text,False
             
        except Exception as e:
            logger.error("Failed during inference: %s", str(e), exc_info=True)
            raise