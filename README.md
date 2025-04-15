1) In a conda prompt, navigate to the project directory:
   cd /path/to/Shamzam

2) Run the Catalogue Service in that prompt:
   python catalog_service.py

3) To test the Catalogue Service, open a NEW conda prompt, navigate to the same directory, and run:
   python -m unittest test_catalog.py

4) Open ANOTHER new conda prompt, navigate to the project directory, and run the Recognition Service (Make sure ENV.txt contains a valid Audd.io key and keep the Catalogue Service from step 2 running.):
   source ENV.txt
   python recognition_service.py

5) To test the Recognition Service, open yet another new conda prompt, navigate to the project directory, and run:
   python -m unittest test_recognition.py
