# StarWarsDataBank

Star Wars DataBank is a Tkinter desktop catalog for browsing Star Wars character data from SWAPI.

## Features

- Browse a full character index instead of only one random record.
- Search by character, homeworld, species, or film.
- Filter by gender and favorites.
- Sort by name, height, mass, birth year, or film count.
- View related films, vehicles, starships, species, and homeworld data.
- Pick a random character, copy a profile summary, or open the API record.
- Cache API data locally so recently loaded records remain available if the network is down.

## Run

```powershell
python .\StarWarsDataBank.py
```

The app uses `https://swapi.info/api/` for live data and stores runtime cache/favorites in the current user's home directory.
