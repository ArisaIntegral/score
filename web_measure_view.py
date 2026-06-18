import queue
import threading
import time
from pathlib import Path

import librosa
import numpy as np
import streamlit as st

from matchmaker import EXAMPLE_PIECES, Matchmaker
from matchmaker.io.audio import BytesAudioStream
from matchmaker.features.audio import ChromagramProcessor


# =========================
# 設定
# =========================

PIECE_NAME = "bach_fugue"
BEATS_PER_MEASURE = 4

SAMPLE_RATE = 22050
HOP_LENGTH = 441


# =========================
# 小節変換
# =========================

def get_measure_position(current_beat, beats_per_measure=4):
    measure_number = int(current_beat // beats_per_measure) + 1
    beat_in_measure = current_beat % beats_per_measure
    return measure_number, beat_in_measure


def audio_file_producer(audio_file, data_queue, play_audio=True):
    """
    音声ファイルを少しずつキューに入れる。
    play_audio=True の場合は、同時にスピーカーから音も鳴らす。
    """
    y, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
    y = y.astype(np.float32)

    chunk_duration = HOP_LENGTH / SAMPLE_RATE

    if play_audio:
        try:
            import sounddevice as sd

            with sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
            ) as output_stream:

                for start in range(0, len(y), HOP_LENGTH):
                    chunk = y[start:start + HOP_LENGTH]

                    if len(chunk) < HOP_LENGTH:
                        chunk = np.pad(chunk, (0, HOP_LENGTH - len(chunk)))

                    # Matchmakerへ送る
                    data_queue.put(chunk.tobytes())

                    # 同時に音を鳴らす
                    output_stream.write(chunk.reshape(-1, 1))

        except Exception as e:
            print(f"Audio playback failed: {e}")
            print("Continue streaming without sound.")

            for start in range(0, len(y), HOP_LENGTH):
                chunk = y[start:start + HOP_LENGTH]

                if len(chunk) < HOP_LENGTH:
                    chunk = np.pad(chunk, (0, HOP_LENGTH - len(chunk)))

                data_queue.put(chunk.tobytes())
                time.sleep(chunk_duration)

    else:
        for start in range(0, len(y), HOP_LENGTH):
            chunk = y[start:start + HOP_LENGTH]

            if len(chunk) < HOP_LENGTH:
                chunk = np.pad(chunk, (0, HOP_LENGTH - len(chunk)))

            data_queue.put(chunk.tobytes())
            time.sleep(chunk_duration)

    data_queue.put(None)


# =========================
# Streamlit UI
# =========================

st.set_page_config(
    page_title="自動譜めくり",
    layout="wide",
)

st.title("自動譜めくり")
st.write("現在小節をリアルタイム表示")

piece = EXAMPLE_PIECES[PIECE_NAME]

score_file = Path(piece["score"])
audio_file = Path(piece["audio"])

st.subheader("使用ファイル")
st.write(f"楽譜ファイル：`{score_file.name}`")
st.write(f"音声ファイル：`{audio_file.name}`")
st.write(f"1小節の拍数：`{BEATS_PER_MEASURE}`")

play_audio = st.checkbox("音声も同時に再生する", value=True)

start_button = st.button("開始")

status_area = st.empty()
current_area = st.empty()
detail_area = st.empty()
measure_area = st.empty()


if start_button:
    status_area.info("準備中...")

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

    
    print("score_file =", score_file)
    print("exists =", score_file.exists())

    mm = Matchmaker(
        score_file=score_file,
        input_type="audio",
        method="arzt",
        stream=stream,
    )

    producer_thread = threading.Thread(
        target=audio_file_producer,
        args=(audio_file, data_queue, play_audio),
        daemon=True,
    )

    producer_thread.start()

    status_area.success("再生・解析中")

    last_measure = None
    start_time = time.time()

    for current_position in mm.run(verbose=False):
        elapsed_time = time.time() - start_time

        measure_number, beat_in_measure = get_measure_position(
            current_position,
            BEATS_PER_MEASURE,
        )

        previous_measure = max(1, measure_number - 1)
        next_measure = measure_number + 1

        if measure_number != last_measure:
            current_area.markdown(f"# 現在：{measure_number}小節目")

            detail_area.write(
                f"音楽時刻：約 {elapsed_time:.2f} 秒 / "
                f"beat={current_position:.2f} / "
                f"小節内 {beat_in_measure:.2f} 拍目"
            )

            col1, col2, col3 = measure_area.columns(3)

            with col1:
                st.subheader("前")
                st.metric(label="前の小節", value=f"{previous_measure}小節目")

            with col2:
                st.subheader("現在")
                st.metric(label="現在の小節", value=f"{measure_number}小節目")

            with col3:
                st.subheader("次")
                st.metric(label="次の小節", value=f"{next_measure}小節目")

            last_measure = measure_number

    status_area.success("終了しました")
