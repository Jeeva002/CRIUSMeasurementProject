import torch
import os
import time
from transformers import pipeline, WhisperForConditionalGeneration, WhisperProcessor, GenerationConfig

repo_path = "sankar-asthramedtech/finetuned_whisper-medium_on_pods_V-1.1"
inference_model = WhisperForConditionalGeneration.from_pretrained(repo_path, token=os.environ["HF_TOKEN"])                                #token=os.environ["HF_TOKEN"]
processor = WhisperProcessor.from_pretrained("openai/whisper-medium")

# Load base config from original Whisper
base_config = GenerationConfig.from_pretrained("openai/whisper-medium")
# Attach it to your finetuned model
inference_model.generation_config = base_config



pipe = pipeline(
    task="automatic-speech-recognition",
    model=inference_model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device_map="auto",
    return_timestamps=True,
    stride_length_s=15,
    generate_kwargs={
        "language": "en",            # set your language (e.g., "en", "ta", "hi")
        "task": "transcribe",
        "num_beams": 1,              # The knowledge comes from training.The quality/style of the answer depends on the decoding strategy (like num_beams).
        "repetition_penalty": 1.0,   # It controls the repeated words provided by the model
        "length_penalty": 1.0        # This controls whether the model prefers shorter or longer outputs.

    }

)


def transcribe(audio):
    start_time = time.time()
    text = pipe(audio)["text"]
    end_time = time.time()
    print(f"Inference took {end_time - start_time:.2f} seconds")
    return text

result = transcribe("/content/Ultra.wav")
print("finetuned whisper result",result)
