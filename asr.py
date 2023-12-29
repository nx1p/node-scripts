# simple asr script prototype for testing


import torch
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor
from transformers.utils import is_flash_attn_2_available
from datasets import load_dataset
import time

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model_id = "distil-whisper/distil-large-v2"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
#model="openai/whisper-large-v3",


model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)


pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device="cuda:0", # or mps for Mac devices
    # model_kwargs={"use_flash_attention_2": is_flash_attn_2_available()},
    model_kwargs={"attn_implementation": "flash_attention_2"},
)

if not is_flash_attn_2_available():
    # enable flash attention through pytorch sdpa
    pipe.model = pipe.model.to_bettertransformer()

dataset = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation", trust_remote_code=True)
sample = dataset[0]["audio"]

print("processing\n")
start = time.time()

outputs = pipe(
#    sample, # "<FILE_NAME>"
    "mictest.mp3",
    chunk_length_s=30,
    batch_size=24,
    return_timestamps=True,
)

end = time.time()
elapsed = end - start
print(f"Processing took {elapsed} seconds\n")
print("\n")
print("output: "+outputs["text"])


print("processing\n")
start = time.time()

outputs = pipe(
#    sample, # "<FILE_NAME>"
    "test.mp3",
    chunk_length_s=30,
    batch_size=24,
    return_timestamps=True,
)

end = time.time()
elapsed = end - start
print(f"Processing took {elapsed} seconds\n")
print("\n")
print("output: "+outputs["text"])