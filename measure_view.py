import queue
import threading
import time
from pathlib import Path

import librosa
import numpy as np

from matchmaker import EXAMPLE_PIECES, Matchmaker
from matchmaker.io.audio import BytesAudioStream
from matchmaker.features.audio import ChromagramProcessor


# =========================
# 設定
# =========================

PIECE_NAME = "canon"
BEATS_PER_MEASURE = 4

SAMPLE_RATE = 22050
HOP_LENGTH = 441  # 22050Hz のとき約0.02秒


def get_measure_position(current_beat, beats_per_measure=4):
    """
    current_beat を小節番号に変換する。
    4/4なら 0〜4拍 = 1小節目、4〜8拍 = 2小節目。
    """
    measure_number = int(current_beat // beats_per_measure) + 1
    beat_in_measure = current_beat % beats_per_measure
    return measure_number, beat_in_measure


def audio_file_producer(audio_file, data_queue):
    """
    音声ファイルを少しずつ読み出して queue に入れる。
    Matchmaker から見ると、マイク入力が少しずつ来ているように見える。
    """
    print(f"Loading audio file: {audio_file.name}")

    y, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
    y = y.astype(np.float32)

    print("Start streaming audio file like microphone input...")

    chunk_duration = HOP_LENGTH / SAMPLE_RATE

    for start in range(0, len(y), HOP_LENGTH):
        chunk = y[start:start + HOP_LENGTH]

        if len(chunk) < HOP_LENGTH:
            chunk = np.pad(chunk, (0, HOP_LENGTH - len(chunk)))

        data_queue.put(chunk.tobytes())

        # ここが重要：
        # 音声ファイルを一気に渡さず、実時間に近い速度で渡す
        time.sleep(chunk_duration)

    data_queue.put(None)
    print("Audio stream finished.")


def main():
    piece = EXAMPLE_PIECES[PIECE_NAME]

    score_file = Path(piece["score"])
    audio_file = Path(piece["audio"])

    print("===================================")
    print("Measure View: File as Microphone")
    print("===================================")
    print(f"Score file : {score_file.name}")
    print(f"Audio file : {audio_file.name}")
    print(f"Beats/measure : {BEATS_PER_MEASURE}")
    print("-----------------------------------")

    data_queue = queue.Queue()

    stream = BytesAudioStream(
        processor=ChromagramProcessor(
            sample_rate=SAMPLE_RATE,
            hop_length=HOP_LENGTH,
        ),
        sample_rate=SAMPLE_RATE,
        hop_length=HOP_LENGTH,
        data_queue=data_queue,
    )

    mm = Matchmaker(
        score_file=score_file,
        input_type="audio",
        method="arzt",
        stream=stream,
    )

    producer_thread = threading.Thread(
        target=audio_file_producer,
        args=(audio_file, data_queue),
        daemon=True,
    )

    producer_thread.start()

    last_measure = None
    start_time = time.time()

    for current_position in mm.run(verbose=False):
        elapsed_time = time.time() - start_time

        measure_number, beat_in_measure = get_measure_position(
            current_position,
            BEATS_PER_MEASURE,
        )

        if measure_number != last_measure:
            print(
                f"音楽時刻 {elapsed_time:.2f}秒："
                f"現在 {measure_number}小節目 "
                f"/ 小節内 {beat_in_measure:.2f}拍目 "
                f"/ beat={current_position:.2f}"
            )
            last_measure = measure_number

    print("-----------------------------------")
    print("Finished.")


if __name__ == "__main__":
    main()