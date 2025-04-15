import unittest
import requests
import sqlite3
import os
import time

class TestShamzamRecognition(unittest.TestCase):
    """
    Tests for the Shamzam Recognition Service (S4).
    """

    def setUp(self):
        """
        1) Clear the 'tracks' table.
        2) Insert a known track that matches a recognized snippet.
        3) Define the base URL for recognition and catalog services.
        """
        # Adjust for your environment
        self.db_path           = "shamzam.db"
        self.catalog_url       = "http://127.0.0.1:5000/catalog/tracks"
        self.recognition_url   = "http://127.0.0.1:6000/recognition"

        if not os.path.exists(self.db_path):
            raise RuntimeError(
                f"Database file '{self.db_path}' does not exist. "
                "Please ensure your services are initialized."
            )

        # 1) Clear the tracks table
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tracks;")
            conn.commit()

        # 2) Insert a known track in the catalog.
        #    Suppose you have a snippet recognized by Audd.io as "Blinding Lights" by "The Weeknd".
        known_track = {"title": "Blinding Lights", "artist": "The Weeknd"}
        rsp_add = requests.post(self.catalog_url, json=known_track)
        # Expect 201 if the catalog service is running
        if rsp_add.status_code != 201:
            self.fail(f"Could not add known track: {rsp_add.text}")

        # Give a slight delay if needed for DB commits (rarely necessary, but sometimes helpful)
        time.sleep(0.2)

    ########################################################################
    # S4: Happy Path
    ########################################################################

    def test_s4_happy_path_recognize_known_track(self):
        """
        1) Have 'Blinding Lights' in the DB (setUp).
        2) Use an audio fragment that Audd.io recognizes as 'Blinding Lights' by 'The Weeknd'.
        3) Expect 200 + JSON with the track's ID, title, artist.
        """
        fragment_file = '_Blinding Lights.wav'
        if not os.path.exists(fragment_file):
            self.skipTest(f"Skipping test: sample file '{fragment_file}' not found.")

        with open(fragment_file, "rb") as f:
            files = {"file": (fragment_file, f, "audio/wav")}
            rsp   = requests.post(self.recognition_url, files=files)
        
        self.assertEqual(rsp.status_code, 200, f"Expected 200, got {rsp.status_code}")
        data = rsp.json()
        self.assertIn("trackId", data)
        self.assertEqual(data["title"], "Blinding Lights")
        self.assertEqual(data["artist"], "The Weeknd")

    ########################################################################
    # S4: Unhappy Path #1: Missing file in request
    ########################################################################

    def test_s4_unhappy_missing_file(self):
        """
        If you send a POST with no file, you should get 400 Bad Request.
        """
        rsp = requests.post(self.recognition_url)  # No 'files' parameter
        self.assertEqual(rsp.status_code, 400, f"Expected 400, got {rsp.status_code}")

    ########################################################################
    # S4: Unhappy Path #2: Recognized track NOT in DB
    ########################################################################

    def test_s4_unhappy_track_not_in_db(self):
        """
        Suppose Audd.io recognizes the snippet as 'Everybody (Backstreet's Back)' by 'Backstreet Boys',
        but you do NOT have that track in our local DB -> Expect 404 from recognition service.
        
        Steps:
         1) Don't add 'Everybody...' to DB
         2) Use '_Everybody (Backstreet’s Back) (Radio Edit).wav' snippet 
         3) Expect 404 because the recognized track isn't in local DB
        """

        fragment_file = "_Everybody (Backstreets Back) (Radio Edit).wav"
        if not os.path.exists(fragment_file):
            self.skipTest(f"Skipping test: sample file '{fragment_file}' not found.")

        with open(fragment_file, "rb") as f:
            files = {"file": (fragment_file, f, "audio/wav")}
            rsp   = requests.post(self.recognition_url, files=files)

        self.assertEqual(rsp.status_code, 404, f"Expected 404, got {rsp.status_code}")
        # Optionally, check the JSON for a "message" key
        self.assertIn("message", rsp.json())

    ########################################################################
    # S4: Unhappy Path #3: Using "Davos.wav" speech (no recognized track)
    ########################################################################

    def test_s4_unhappy_davos_no_match(self):
        """
        Use 'Davos.wav', which is a speech fragment (Donald Trump at WEF).
        Audd.io likely won't recognize it as a known music track.
        => Expect 404 from recognition service.
        """
        fragment_file = "_Davos.wav"
        if not os.path.exists(fragment_file):
            self.skipTest(f"Skipping test: sample file '{fragment_file}' not found.")

        with open(fragment_file, "rb") as f:
            files = {"file": (fragment_file, f, "audio/wav")}
            rsp   = requests.post(self.recognition_url, files=files)

        # If the external API doesn't return a recognized "title"/"artist", our service returns 404
        self.assertEqual(rsp.status_code, 404, f"Expected 404, got {rsp.status_code}")
        data = rsp.json()
        self.assertIn("message", data)


if __name__ == "__main__":
    unittest.main()
