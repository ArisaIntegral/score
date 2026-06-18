from pathlib import Path
from _queue import Empty

from matchmaker import EXAMPLE_PIECES, Matchmaker


PIECE_NAME = "canon"
BEATS_PER_MEASURE = 4


def get_measure_position(current_beat, beats_per_measure=4):
    measure_number = int(current_beat // beats_per_measure) + 1
    beat_in_measure = current_beat % beats_per_measure
    return measure_number, beat_in_measure


def main():
    piece = EXAMPLE_PIECES[PIECE_NAME]
    score_file = Path(piece["score"])

    print("===================================")
    print("Live Measure View")
    print("===================================")
    print(f"Score file      : {score_file.name}")
    print("Input           : microphone / live audio")
    print(f"Beats / measure : {BEATS_PER_MEASURE}")
    print("-----------------------------------")
    print("マイク入力を待っています。演奏を始めてください。")
    print("終了するときは Ctrl + C")
    print("-----------------------------------")

    try:
        mm = Matchmaker(
            score_file=score_file,
            input_type="audio",
            method="arzt",
        )
    except Empty as e:
        print(f"Error initializing Matchmaker: {e}")
        return

    last_measure = None

    try:
        for current_position in mm.run(verbose=False):
            measure_number, beat_in_measure = get_measure_position(
                current_position,
                BEATS_PER_MEASURE,
            )

            if measure_number != last_measure:
                print(
                    f"現在：{measure_number}小節目 "
                    f"/ 小節内 {beat_in_measure:.2f}拍目 "
                    f"/ beat={current_position:.2f}"
                )
                last_measure = measure_number

    except KeyboardInterrupt:
        print()
        print("終了しました。")


if __name__ == "__main__":
    main()