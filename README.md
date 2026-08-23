# courses

**<https://stolaf.dev/courses>**

Browse the St. Olaf course catalog with [Datasette](https://datasette.io/), running
entirely in the browser via [datasette-lite](https://github.com/simonw/datasette-lite).

By default the page loads `https://stolaf.dev/course-data/catalog-recent.db`, which holds
sections, instructors, general education requirements and meeting times as related
tables. All of the datasette-lite query parameters still work, so `?url=`, `?csv=`,
`?json=`, `?parquet=`, `?sql=` and `?memory=1` load other data instead of the catalog.

## Development

```sh
./serve.sh   # http://localhost:8009
./test.sh    # end-to-end tests against the real catalog
```

The tests drive a real browser with Playwright and download the published catalog,
so they need network access.
