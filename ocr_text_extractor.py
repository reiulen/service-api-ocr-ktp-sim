from google.cloud import vision_v1
from google.cloud.vision_v1 import types
from google.cloud import storage
from google.protobuf.json_format import MessageToDict
import pandas as pd
import numpy as np
import sys
import json
import kyc_config as cfg
import re

client = vision_v1.ImageAnnotatorClient.from_service_account_file(cfg.gcv_api_key_path)

def get_text_response_from_path(path):
    output = None

    try:
        if path.startswith('http') or path.startswith('gs:'):
            image = types.Image()
            image.source.image_uri = path
        else:
            with open(path, 'rb') as image_file:
                content = image_file.read()
            image = types.Image(content=content)

    except ValueError:
        output = "Cannot Read Input File"
        return output

    response = client.text_detection(image=image)
    text_full_annotations = response.full_text_annotation.text
    text_annotations = response.text_annotations[0].description
    
    lines = text_annotations.split("\n")
    res = []
    for line in lines:
        line = re.sub('|/|gol. darah|nik|ΝΙΚ|kewarganegaraan|nama|status perkawinan|berlaku hingga|alamat|agama|tempat/tgl lahir|jenis kelamin|gol darah|rt/rw|kel|desa|kecamatan', '', line, flags=re.IGNORECASE)
        line = line.replace(":","").strip()
        if line != "":
            res.append(line)

    response = {}
    if "ΝΙΚ" in text_annotations or "Nama" in text_annotations or "Tempat/Tgl Lahir" in text_annotations:
        response = {
            "no_identitas": res[2],
            "nama": res[3],
            "alamat": f"{res[6]} RT/RW {res[7]} Kel/Desa {res[8]} Kecamatan {res[9]}",
            "jenis_indentitas" : 'KTP'
        }
        return response

    sim_pattern = re.compile(r'(?P<nomor>\d+-\d+-\d+)\n'
                         r'(?P<nama>.*?)\n'
                         r'(?P<tempat_tanggal_lahir>.*?)\n'
                         r'(?P<jenis_kelamin>.*?)\n'
                         r'(?P<alamat_line_1>.*?)\n'
                         r'(?P<alamat_line_2>.*?)\n'
                         r'(?P<alamat_line_3>.*?)\n'
                         r'(?P<berlaku_hingga>.*?)$',
                         re.MULTILINE | re.DOTALL)

    match_sim = sim_pattern.search(text_full_annotations)
    if match_sim : 
        alamat = f"{match_sim.group('alamat_line_1')} {match_sim.group('alamat_line_2')} {match_sim.group('alamat_line_3')}"
        response = {
            "no_identitas":  match_sim.group("nomor"),
            "nama": re.sub(r'^\d+\.\s*', '', match_sim.group("nama")),
            "alamat": re.sub(r'^\d+\.\s*', '',alamat),
            "jenis_indentitas" : 'SIM'
        }
        return response
    return {}

def process_ocr(img_path):
    text_response = get_text_response_from_path(img_path)
    return text_response

if __name__ == '__main__':
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        print('OCR processing ' + img_path)
        process_ocr(img_path)
    else:
        print('Argument is missing: image path')
