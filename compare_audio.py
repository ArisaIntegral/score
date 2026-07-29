import librosa
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ここを書き換えてください
ref_path = r"debug_generated_score.wav"
perf_path = r"bach_cello1_sample.mp3"

sr = 44100

def load_audio(path):
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y.astype(np.float32)

def first_onset_time(y, sr):
    # RMSでざっくり最初の音を検出
    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(
        y=y,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]

    threshold = max(1e-6, np.max(rms) * 0.05)
    idx = np.where(rms > threshold)[0]

    if len(idx) == 0:
        return None

    return idx[0] * hop_length / sr

ref = load_audio(ref_path)
perf = load_audio(perf_path)

ref_dur = len(ref) / sr
perf_dur = len(perf) / sr

ref_onset = first_onset_time(ref, sr)
perf_onset = first_onset_time(perf, sr)

print("==== Duration ====")
print(f"reference:   {ref_dur:.3f} sec")
print(f"performance: {perf_dur:.3f} sec")
print(f"diff:        {perf_dur - ref_dur:.3f} sec")

print()
print("==== First onset ====")
print(f"reference first onset:   {ref_onset:.3f} sec")
print(f"performance first onset: {perf_onset:.3f} sec")
print(f"offset perf - ref:       {perf_onset - ref_onset:.3f} sec")

# waveform plot
t_ref = np.arange(len(ref)) / sr
t_perf = np.arange(len(perf)) / sr

plt.figure(figsize=(14, 6))

plt.subplot(2, 1, 1)
plt.plot(t_ref, ref)
plt.title("Reference: debug_generated_score.wav")
plt.xlim(0, min(5, ref_dur))

plt.subplot(2, 1, 2)
plt.plot(t_perf, perf)
plt.title("Performance audio")
plt.xlim(0, min(5, perf_dur))

plt.tight_layout()
plt.savefig("audio_compare_waveform.png", dpi=150)
print()
print("saved: audio_compare_waveform.png")