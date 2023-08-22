Ensure [poetry](https://python-poetry.org/docs/#installation) is installed

If you use VSCode, to have Intellisense work with poetry, use

```sh
poetry config virtualenvs.in-project true
```

### Install dependencies

```sh
poetry install
```

### Run crawler

```sh
poetry shell
python3 -m crawler.main
```

### Dump contents of LMDB

```sh
python3 -m crawler.dump --max_links {MAX_LINKS}
```

This will dump the contents of the LMDB to `dump.txt`
