import os
from flask import Flask, jsonify, request
from ocr_text_extractor import process_ocr
from datetime import datetime

app = Flask(__name__)

@app.route('/api/scan-image', methods=['POST'])
def scan_ktp():
    form = request.files
    image_form = form.get('image')

    try:
        if image_form:
            directory = os.path.join(app.instance_path, 'images-scan')
            if not os.path.exists(directory):
                os.makedirs(directory)

            image_path = f"images-scan/{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            image_form.save(os.path.join(app.instance_path, image_path))
        else :
            return jsonify({
                "status": False,
                'message': 'Tidak ada gambar yang di upload'
            })
        
        image_path = f"instance/{image_path}"
        scan_image = process_ocr(image_path)
        if scan_image :
            return jsonify({
                "status": True,
                "data" : scan_image,
                "directory_image" : image_path
            })
        else :
            return jsonify({
                "status": False,
                "message": "Tidak dapat membaca data dari gambar"
            })
        
    except Exception as e:
        return jsonify({
            "status": False,
            "message": str(e)
        })


if __name__ == "__main__":
    app.run(host='0.0.0.0')
