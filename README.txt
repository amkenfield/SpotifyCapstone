Site Title : Track Unpacker

Site URL : https://spotify-capstone.herokuapp.com/

Description: This website allows for users to search both the site database as well as Spotify for individual musical tracks,
	     and to "unpack" the details of each track's AudioFeatures as assigned by Spotify.

User Flow: The site's landing page greets an unlogged-in user and directs them to a sign-up page.
	   The user enters their preferred username, email, and password, and is then added to the site's database and logged in.
	   At this point, the user is prompted to search the site's database for track(s) corresponding to their search query.
	   They are presented with the results, and if none are found, are prompted to search instead the Spotify track library.
	   This Spotify search will automatically add to the site database any tracks not yet added.
	   In this way, the site database will gradually accumulate a set of Tracks data.
	   The user is able to add each individual track to their user library, which is accessed through the navbar.
	   Each individual track in the site database is expandable to its own page, which lists the "unpacked" track information with Spotify's AudioFeatures categories.
	   Descriptions for the categories are on a distinct 'Categories' page, also accessed through the navbar.

API: This site uses the Spotify API (https://api.spotify.com), by means of the Spotipy Python library (https://spotipy.readthedocs.io/en/2.18.0).

Technology Stack: This site uses the Flask framework in Python, a PostgreSQL database, and SQLAlchemy as an ORM.