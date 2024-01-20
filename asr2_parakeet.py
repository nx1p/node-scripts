import nemo.collections.asr as nemo_asr
import time

asr_model = nemo_asr.models.EncDecRNNTBPEModel.from_pretrained(model_name="nvidia/parakeet-rnnt-1.1b")


print("processing\n")
start = time.time()

transcription = asr_model.transcribe(['mictest-16khz.wav'])[0][0]

end = time.time()
elapsed = end - start
print(f"Processing took {elapsed} seconds\n")
print("\n")
print(f"output: {transcription}")

print("processing\n")
start = time.time()

transcription = asr_model.transcribe(['mictest-16khz.wav'])[0][0]

end = time.time()
elapsed = end - start
print(f"Processing took {elapsed} seconds\n")
print("\n")
print(f"output: {transcription}")