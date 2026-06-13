from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sqlite3
import exifread
from PIL import Image
from PyPDF2 import PdfReader
import docx
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Database Setup ----------------
def init_db():
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        filetype TEXT,
        metadata TEXT,
        gps_lat REAL,
        gps_lon REAL,
        date_extracted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_to_db(filepath, ext, extracted_metadata, lat=None, lon=None):
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO metadata_records (filename, filetype, metadata, gps_lat, gps_lon) VALUES (?, ?, ?, ?, ?)",
        (filepath, ext, extracted_metadata, lat, lon)
    )
    conn.commit()
    conn.close()

# ---------------- GPS Conversion ----------------
def dms_to_decimal(dms, ref):
    degrees = dms.values[0].num / dms.values[0].den
    minutes = dms.values[1].num / dms.values[1].den
    seconds = dms.values[2].num / dms.values[2].den
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal *= -1
    return decimal

# ---------------- Routes ----------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    result = {}
    metadata_str = ""
    lat, lon = None, None

    try:
        if ext in ['.jpg', '.jpeg']:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            exif_data = {str(tag): str(tags[tag]) for tag in tags}
            metadata_str = str(exif_data)

            gps_lat     = tags.get('GPS GPSLatitude')
            gps_lat_ref = tags.get('GPS GPSLatitudeRef')
            gps_lon     = tags.get('GPS GPSLongitude')
            gps_lon_ref = tags.get('GPS GPSLongitudeRef')

            if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
                lat = dms_to_decimal(gps_lat, str(gps_lat_ref))
                lon = dms_to_decimal(gps_lon, str(gps_lon_ref))

            result = {
                'type': 'JPEG',
                'fields': exif_data,
                'gps': {'lat': lat, 'lon': lon} if lat else None
            }

        elif ext == '.png':
            image = Image.open(filepath)
            fields = {
                'Format':   image.format or 'PNG',
                'Width':    str(image.size[0]) + ' px',
                'Height':   str(image.size[1]) + ' px',
                'Mode':     image.mode,
                'Filename': file.filename,
                'Note':     'PNG images do not usually store EXIF metadata.'
            }
            metadata_str = str(fields)
            result = {'type': 'PNG', 'fields': fields, 'gps': None}

        elif ext == '.pdf':
            reader = PdfReader(filepath)
            meta = reader.metadata or {}
            fields = {str(k): str(v) for k, v in meta.items()} if meta else {'Info': 'No metadata found in PDF.'}
            metadata_str = str(fields)
            result = {'type': 'PDF', 'fields': fields, 'gps': None}

        elif ext == '.docx':
            doc_obj = docx.Document(filepath)
            cp = doc_obj.core_properties
            fields = {
                'Author':           str(cp.author),
                'Title':            str(cp.title),
                'Subject':          str(cp.subject),
                'Description':      str(cp.description),
                'Keywords':         str(cp.keywords),
                'Last Modified By': str(cp.last_modified_by),
                'Revision':         str(cp.revision),
                'Created':          str(cp.created),
                'Modified':         str(cp.modified),
            }
            metadata_str = str(fields)
            result = {'type': 'DOCX', 'fields': fields, 'gps': None}

        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        save_to_db(file.filename, ext, metadata_str, lat, lon)
        return jsonify({'success': True, **result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route('/records', methods=['GET'])
def records():
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, filetype, gps_lat, gps_lon, date_extracted FROM metadata_records ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    data = [
        {
            'id':             r[0],
            'filename':       r[1],
            'filetype':       r[2],
            'gps_lat':        r[3],
            'gps_lon':        r[4],
            'date_extracted': r[5]
        }
        for r in rows
    ]
    return jsonify(data)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
