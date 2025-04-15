import unittest
import requests
import sqlite3
import os

class TestShamzamCatalogue(unittest.TestCase):
    """
    Tests for Shamzam's Catalogue Service (S1, S2, S3).

    Each user story has:
      - 1 "happy path" test
      - 3 "unhappy path" tests
    """

    def setUp(self):
        """
        Called before each test method.

        1) Clear the 'tracks' table in shamzam.db so each test starts clean.
        2) Set base_url to local Flask instance (catalog_service.py).
        """
        # Adjust 'shamzam.db' path if needed
        db_path = "shamzam.db"
        if not os.path.exists(db_path):
            raise RuntimeError(
                f"Database file '{db_path}' does not exist. "
                "Please ensure catalog_service.py has initialized it."
            )
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM tracks;")
            conn.commit()

        # Point to your locally running Flask service
        self.base_url = "http://127.0.0.1:5000/catalog/tracks"

    ########################################################################
    # S1: Add a track
    ########################################################################

    def test_s1_happy_path_add_track(self):
        """
        Happy Path: Add a valid track.
        Expect 201 Created and a success message.
        """
        data = {"title": "Don't Look Back In Anger", "artist": "Oasis"}
        rsp  = requests.post(self.base_url, json=data)
        self.assertEqual(rsp.status_code, 201)
        self.assertIn("message", rsp.json())

    def test_s1_unhappy_missing_title(self):
        """
        Unhappy Path #1 for S1:
        Missing 'title' field -> Expect 400 Bad Request
        """
        data = {"artist": "Oasis"}
        rsp  = requests.post(self.base_url, json=data)
        self.assertEqual(rsp.status_code, 400)

    def test_s1_unhappy_missing_artist(self):
        """
        Unhappy Path #2 for S1:
        Missing 'artist' field -> Expect 400 Bad Request
        """
        data = {"title": "Don't Look Back In Anger"}
        rsp  = requests.post(self.base_url, json=data)
        self.assertEqual(rsp.status_code, 400)

    def test_s1_unhappy_empty_strings(self):
        """
        Unhappy Path #3 for S1:
        Title or artist is empty -> Expect 400 Bad Request
        """
        data = {"title": "", "artist": ""}
        rsp  = requests.post(self.base_url, json=data)
        self.assertEqual(rsp.status_code, 400)

    ########################################################################
    # S2: Remove a track
    ########################################################################

    def test_s2_happy_path_remove_track(self):
        """
        Happy Path: 
        1) Add a track
        2) Fetch its ID
        3) Remove it
        Expect 201 for creation, 200 for removal.
        """
        # 1) Add a track to remove
        data_add = {"title": "SongToRemove", "artist": "UnitTestBand"}
        rsp_add  = requests.post(self.base_url, json=data_add)
        self.assertEqual(rsp_add.status_code, 201)

        # 2) List tracks, find newly added
        rsp_list = requests.get(self.base_url)
        self.assertEqual(rsp_list.status_code, 200)
        tracks   = rsp_list.json().get("tracks", [])

        track_id = None
        for t in tracks:
            if t["title"] == "SongToRemove" and t["artist"] == "UnitTestBand":
                track_id = t["id"]
                break
        self.assertIsNotNone(track_id, "Couldn't find newly added track.")

        # 3) Remove it
        delete_url = f"{self.base_url}/{track_id}"
        rsp_del    = requests.delete(delete_url)
        self.assertEqual(rsp_del.status_code, 200)

    def test_s2_unhappy_nonexistent_id(self):
        """
        Unhappy Path #1 for S2:
        Deleting a track that doesn't exist -> Expect 404
        """
        delete_url = f"{self.base_url}/999999"
        rsp = requests.delete(delete_url)
        self.assertEqual(rsp.status_code, 404)

    def test_s2_unhappy_negative_id(self):
        """
        Unhappy Path #2 for S2:
        Negative track id -> Likely 404 (not found).
        """
        delete_url = f"{self.base_url}/-5"
        rsp = requests.delete(delete_url)
        self.assertEqual(rsp.status_code, 404)

    def test_s2_unhappy_noninteger_id(self):
        """
        Unhappy Path #3 for S2:
        Non-integer track ID -> Flask route mismatch => 404 Not Found
        """
        delete_url = f"{self.base_url}/abc"
        rsp = requests.delete(delete_url)
        self.assertEqual(rsp.status_code, 404)

    ########################################################################
    # S3: List all tracks
    ########################################################################

    def test_s3_happy_path_list_tracks(self):
        """
        Happy Path: 
        1) Start with an empty DB (cleared by setUp).
        2) Add multiple known tracks.
        3) GET /catalog/tracks
        4) Verify the returned list matches the tracks you added.
        """

        # Step 1: The DB is already empty due to setUp() calling DELETE FROM tracks.

        # Step 2: Add known tracks
        test_tracks = [
            {"title": "Song A", "artist": "Artist A"},
            {"title": "Song B", "artist": "Artist B"},
            {"title": "Song C", "artist": "Artist C"},
        ]
        for track in test_tracks:
            rsp_add = requests.post(self.base_url, json=track)
            self.assertEqual(rsp_add.status_code, 201, "Failed to add track")

        # Step 3: GET /catalog/tracks
        rsp = requests.get(self.base_url)
        self.assertEqual(rsp.status_code, 200, f"Expected 200, got {rsp.status_code}")

        data = rsp.json()
        self.assertIn("tracks", data, "Response JSON missing 'tracks' key.")
        returned_tracks = data["tracks"]

        # Step 4: Verify the returned list contains exactly the tracks you added
        #  (IDs will differ, so compare title & artist)
        self.assertEqual(len(returned_tracks), len(test_tracks),
                        "Number of returned tracks does not match what you added.")

        for expected in test_tracks:
            found = any(
                rt["title"] == expected["title"] and rt["artist"] == expected["artist"]
                for rt in returned_tracks
            )
            self.assertTrue(found, f"Track {expected} not found in returned list.")

    def test_s3_unhappy_method_not_allowed(self):
        """
        Unhappy Path #1 for S3:
        Using PUT instead of GET -> Expect 405 Method Not Allowed
        """
        rsp = requests.put(self.base_url)
        self.assertEqual(rsp.status_code, 405)

    def test_s3_unhappy_subpath_405(self):
        """
        Unhappy Path #2 for S3:
        GET on /catalog/tracks/<id> which doesn't exist as a 'list' endpoint.
        The route is only defined for DELETE in the code.
        => Expect 405 Method Not Allowed
        """
        rsp = requests.get(f"{self.base_url}/999999")
        self.assertEqual(rsp.status_code, 405)

    def test_s3_unhappy_incorrect_endpoint(self):
        """
        Unhappy Path #3 for S3:
        GET on a misspelled endpoint /catalog/trakcs 
        => Expect 404 Not Found
        """
        bad_url = "http://127.0.0.1:5000/catalog/trakcs"
        rsp     = requests.get(bad_url)
        self.assertEqual(rsp.status_code, 404)


if __name__ == '__main__':
    unittest.main()
