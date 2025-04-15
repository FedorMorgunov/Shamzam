"""
Implements one endpoint:
  1. POST /recognition  (S4) Recognize a music fragment using Audd.io
"""

import os
import requests
import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'shamzam.db'

# Replace with your Audd.io API key or load from environment:
AUDD_API_KEY = os.getenv("AUDD_KEY", "58977ae53d1f86fc1c60737be53d4d3d")

def get_db():
    """Returns a SQLite connection, stored in Flask’s 'g' context."""
    if 'db_conn' not in g:
        g.db_conn = sqlite3.connect(DATABASE)
        g.db_conn.row_factory = sqlite3.Row
    return g.db_conn

@app.teardown_appcontext
def close_db(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

@app.route("/recognition", methods=["POST"])
def recognize_fragment():
    """
    S4: Convert an audio fragment to a known track in the catalogue.
    Expects a file upload in form-data with key 'file'.

    Workflow:
      1) Send fragment to Audd.io
      2) Compare recognized title/artist with local DB
      3) Return match if found, else 404
    """
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    # Send file to Audd.io
    url = "https://api.audd.io/"
    data = {
        "api_token": AUDD_API_KEY,
        "return": "apple_music,spotify"  # example of additional data
    }
    files = {
        "file": (audio_file.filename, audio_file, audio_file.content_type)
    }

    try:
        response = requests.post(url, data=data, files=files, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"message": f"Error calling Audd.io: {str(e)}"}), 500

    result = response.json()
    print("DEBUG Audd.io response:", result)
    if result.get("status") == "success":
        recognized = result.get("result", {})
        if recognized is not None:
            recognized_title = recognized.get("title")
            recognized_artist = recognized.get("artist")

            # Now see if we have this track in our 'tracks' table
            db = get_db()
            cursor = db.cursor()
            # Simple approach: see if there's an exact match
            cursor.execute("""
                SELECT id, title, artist
                FROM tracks
                WHERE LOWER(title) = LOWER(?)
                AND LOWER(artist) = LOWER(?)
                """, (recognized_title, recognized_artist))
            row = cursor.fetchone()

            if row:
                # We found a match
                return jsonify({
                    "trackId": row["id"],
                    "title": row["title"],
                    "artist": row["artist"]
                }), 200
            else:
                # Not found in our local catalogue
                return jsonify({"message": "No matching track in catalogue"}), 404
        else:
            # Snippet not recognized by Aaud.io
            return jsonify({"message": "Track not recognized"}), 404
    else:
        # Likely invalid Aaud.io key
        return jsonify({"message": result.get("error").get("error_message")}), 404


if __name__ == "__main__":
    # This service assumes the same DB schema as 'catalog_service.py'.
    # Make sure 'shamzam.db' and its 'tracks' table are already created.
    app.run(port=6000, debug=True)
