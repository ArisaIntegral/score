import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil


def force_mxl_cello(input_mxl, output_mxl):
    input_mxl = Path(input_mxl)
    output_mxl = Path(output_mxl)

    tmp_dir = input_mxl.with_suffix("")
    tmp_dir = Path(str(tmp_dir) + "_unpacked")

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1. mxlを展開
    with zipfile.ZipFile(input_mxl, "r") as z:
        z.extractall(tmp_dir)

    # 2. container.xmlから本体MusicXMLの場所を読む
    container_path = tmp_dir / "META-INF" / "container.xml"
    container_tree = ET.parse(container_path)
    container_root = container_tree.getroot()

    ns_container = {}
    if container_root.tag.startswith("{"):
        uri = container_root.tag.split("}")[0][1:]
        ns_container = {"c": uri}
        rootfile_elem = container_root.find(".//c:rootfile", ns_container)
    else:
        rootfile_elem = container_root.find(".//rootfile")

    if rootfile_elem is None:
        raise RuntimeError("rootfile not found in META-INF/container.xml")

    musicxml_relpath = rootfile_elem.attrib["full-path"]
    musicxml_path = tmp_dir / musicxml_relpath

    # 3. MusicXMLを編集
    tree = ET.parse(musicxml_path)
    root = tree.getroot()

    # namespace対応
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0][1:]

        def q(tag):
            return f"{{{ns_uri}}}{tag}"

        score_parts = root.findall(".//" + q("score-part"))
    else:
        def q(tag):
            return tag

        score_parts = root.findall(".//score-part")

    if not score_parts:
        raise RuntimeError("score-part not found")

    for score_part in score_parts:
        part_id = score_part.attrib.get("id", "P1")
        inst_id = f"{part_id}-I1"

        # part-nameをCelloに
        part_name = score_part.find(q("part-name"))
        if part_name is None:
            part_name = ET.SubElement(score_part, q("part-name"))
        part_name.text = "Cello"

        # score-instrument
        score_inst = score_part.find(q("score-instrument"))
        if score_inst is None:
            score_inst = ET.SubElement(score_part, q("score-instrument"), {"id": inst_id})
        else:
            score_inst.set("id", inst_id)

        inst_name = score_inst.find(q("instrument-name"))
        if inst_name is None:
            inst_name = ET.SubElement(score_inst, q("instrument-name"))
        inst_name.text = "Cello"

        # midi-instrument
        midi_inst = score_part.find(q("midi-instrument"))
        if midi_inst is None:
            midi_inst = ET.SubElement(score_part, q("midi-instrument"), {"id": inst_id})
        else:
            midi_inst.set("id", inst_id)

        midi_channel = midi_inst.find(q("midi-channel"))
        if midi_channel is None:
            midi_channel = ET.SubElement(midi_inst, q("midi-channel"))
        midi_channel.text = "1"

        midi_program = midi_inst.find(q("midi-program"))
        if midi_program is None:
            midi_program = ET.SubElement(midi_inst, q("midi-program"))

        # MusicXML / General MIDI: Cello = 43
        midi_program.text = "43"

        volume = midi_inst.find(q("volume"))
        if volume is None:
            volume = ET.SubElement(midi_inst, q("volume"))
        volume.text = "80"

        pan = midi_inst.find(q("pan"))
        if pan is None:
            pan = ET.SubElement(midi_inst, q("pan"))
        pan.text = "0"

    tree.write(musicxml_path, encoding="utf-8", xml_declaration=True)

    # 4. mxlに再圧縮
    if output_mxl.exists():
        output_mxl.unlink()

    with zipfile.ZipFile(output_mxl, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in tmp_dir.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(tmp_dir).as_posix())

    print(f"saved: {output_mxl}")


if __name__ == "__main__":
    force_mxl_cello(
        "bach_cello1.mxl",
        "bach_cello1_force_cello.mxl",
    )