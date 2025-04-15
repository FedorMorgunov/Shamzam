"""
Implements three endpoints:
  1. POST   /catalog/tracks        (S1) Add a track
  2. DELETE /catalog/tracks/<id>   (S2) Remove a track
  3. GET    /catalog/tracks        (S3) List all tracks
"""

import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'shamzam.db'

def get_db():
    """Returns a SQLite connection, stored in Flask’s 'g' context."""
    if 'db_conn' not in g:
        g.db_conn = sqlite3.connect(DATABASE)
        g.db_conn.row_factory = sqlite3.Row  # so we can get columns by name
    return g.db_conn

@app.teardown_appcontext
def close_db(exception):
    """Closes the database connection at the end of each request."""
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

def init_db():
    """Creates the 'tracks' table if it doesn’t exist."""
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/catalog/tracks", methods=["POST"])
def add_track():
    """
    S1: Add a new track to the catalogue.
    Expects JSON: { "title": "...", "artist": "..." }
    Returns 201 Created on success, 400 if bad data.
    """
    data = request.get_json()
    if not data or "title" not in data or "artist" not in data:
        return jsonify({"message": "Missing title or artist"}), 400
    
    title = data["title"].strip()
    artist = data["artist"].strip()
    if not title or not artist:
        return jsonify({"message": "Invalid title or artist"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO tracks (title, artist) VALUES (?, ?)",
                   (title, artist))
    db.commit()
    
    return jsonify({"message": "Track created successfully"}), 201

@app.route("/catalog/tracks/<int:track_id>", methods=["DELETE"])
def remove_track(track_id):
    """
    S2: Remove an existing track from the catalogue.
    Returns 200 OK on success, 404 if track not found.
    """
    db = get_db()
    cursor = db.cursor()
    
    # Check if track exists
    cursor.execute("SELECT id FROM tracks WHERE id = ?", (track_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"message": "Track not found"}), 404
    
    # Delete if found
    cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    db.commit()
    return jsonify({"message": "Track removed successfully"}), 200

@app.route("/catalog/tracks", methods=["GET"])
def list_tracks():
    """
    S3: Return a list of tracks in the catalogue.
    Returns 200 OK with JSON: { "tracks": [ { id, title, artist }, ... ] }
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, title, artist FROM tracks")
    rows = cursor.fetchall()

    tracks = []
    for row in rows:
        tracks.append({
            "id":     row["id"],
            "title":  row["title"],
            "artist": row["artist"]
        })
    
    return jsonify({"tracks": tracks}), 200


if __name__ == "__main__":
    init_db()
    app.run(port=5000, debug=True)
