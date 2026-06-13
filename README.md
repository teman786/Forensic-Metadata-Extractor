GitHub Forensic Metadata Extractor
Overview

GitHub Forensic Metadata Extractor is a digital forensics tool built with Python that extracts and analyzes metadata from PDF documents and JPG/JPEG image files. The tool helps investigators, researchers, and security professionals identify valuable forensic artifacts such as timestamps, author information, device details, GPS coordinates, and geolocation data.

When GPS metadata is available, the tool can generate a Google Maps location link to assist with location-based investigations.

Features
Extract metadata from PDF files
Extract EXIF metadata from JPG/JPEG images
Display file creation and modification timestamps
Retrieve device and camera information (when available)
Extract GPS coordinates from images
Generate Google Maps links from GPS data
Store extracted metadata in SQLite database
User-friendly web interface
Organized metadata reporting for forensic analysis
Technologies Used
Python
SQLite
HTML
CSS

Project Structure
project/
│
├── app.py
├── database.db
├── templates/
│   ├── index.html
│   └── results.html
│
├── static/
│   ├── style.css
│
├── uploads/
│
└── README.md

How It Works
Upload a PDF or JPG/JPEG file.
The application analyzes the file metadata.
Relevant forensic information is extracted.
Metadata is stored in an SQLite database.
Results are displayed through the web interface.
If GPS coordinates are found, a Google Maps location link is generated.
Use Cases
Digital Forensics
Incident Response
OSINT Investigations
Metadata Analysis
