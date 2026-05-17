# StarWarsDataBank

StarWarsDataBank is a Python Tkinter desktop app for browsing Star Wars character data from SWAPI. It keeps the original random-character idea and expands it into a searchable character catalog with richer profile details.

## Features

- Browse a full character index.
- Search characters by name, homeworld, species, or film.
- Filter by gender or favorites.
- Sort by name, height, mass, birth year, or film count.
- View profile details including height, mass, birth year, gender, homeworld, species, films, vehicles, and starships.
- Pick a random character.
- Save favorite characters locally.
- Copy a character summary to the clipboard.
- Open the source API record in a browser.
- Cache API data locally so recently loaded records can still be shown if the network is unavailable.

## Requirements

- Python 3.10 or newer
- `requests`
- Tkinter, which is included with most standard Python installations on Windows

Install the Python dependency:

```powershell
pip install requests
```

## Run

From the project folder:

```powershell
python .\StarWarsDataBank.py
```

## Data Source

The app reads live Star Wars data from:

```text
https://swapi.info/api/
```

Runtime cache and favorites are stored in the current user's home directory:

- `.starwars_databank_cache.json`
- `.starwars_databank_favorites.json`

These files are generated automatically and are not required in the repository.

## Controls

- `Random`: select a random visible character.
- `Refresh`: reload live API data.
- `Previous` / `Next`: move through the current filtered list.
- `Favorite`: save or remove the selected character from favorites.
- `Copy`: copy a readable character summary.
- `API`: open the selected character's API record.
- Right-click menu: quick access to random, favorite, copy, and exit actions.

## Troubleshooting

If the app does not start, confirm Python is installed and `requests` is available:

```powershell
python --version
python -m pip show requests
```

If live data fails to load, check the network connection and try `Refresh`. If cached data exists, the app will continue using it.

## Project Files

- `StarWarsDataBank.py`: main desktop application.
- `favicon.ico`: window icon.
- `README.md`: project documentation.
- `CODE_OF_CONDUCT.md`: community standards.

## License

This project includes a `LICENSE` file. Review it before redistributing or modifying the project.
