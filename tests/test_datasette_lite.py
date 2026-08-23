import json
from playwright.sync_api import Browser, Page, expect
from subprocess import Popen, PIPE
import pathlib
import pytest
import time
from http.client import HTTPConnection

root = pathlib.Path(__file__).parent.parent.absolute()

# Downloading and opening the course catalog takes longer than a fixtures.db
LOAD_TIMEOUT = 180 * 1000


@pytest.fixture(scope="module")
def static_server():
    process = Popen(
        ["python", "-m", "http.server", "8123", "--directory", root], stdout=PIPE
    )
    retries = 5
    while retries > 0:
        conn = HTTPConnection("localhost:8123")
        try:
            conn.request("HEAD", "/")
            response = conn.getresponse()
            if response is not None:
                yield process
                break
        except ConnectionRefusedError:
            time.sleep(1)
            retries -= 1

    if not retries:
        raise RuntimeError("Failed to start http server")
    else:
        process.terminate()
        process.wait()


def load_page(browser: Browser, query_string: str = "") -> Page:
    page = browser.new_page()
    page.goto("http://localhost:8123/" + query_string)
    loading = page.locator("#loading-indicator")
    expect(loading).to_have_css("display", "none", timeout=LOAD_TIMEOUT)
    return page


@pytest.fixture(scope="module")
def dslite(static_server, browser: Browser) -> Page:
    return load_page(browser)


def test_initial_load(dslite: Page):
    expect(dslite.locator("#loading-indicator")).to_have_css("display", "none")


def test_default_loads_course_catalog(dslite: Page):
    assert [el.inner_text() for el in dslite.query_selector_all("h2")] == ["catalog-recent"]


def test_catalog_has_expected_tables(dslite: Page):
    h2 = dslite.query_selector("h2")
    h2.query_selector("a").click()
    expect(dslite).to_have_title("catalog-recent")
    table_names = {
        el.inner_text() for el in dslite.query_selector_all("div.db-table h3 a")
    }
    assert {"section", "instructor", "gereq", "offering"} <= table_names


def test_can_query_section_table(static_server, browser: Browser):
    page = load_page(browser, "#/catalog-recent?sql=select+count(*)+from+section")
    table = page.query_selector("table.rows-and-columns")
    count = int(table.query_selector("tbody td").inner_text())
    assert count > 0
    page.close()


def test_csv_url_overrides_the_default(static_server, browser: Browser):
    page = load_page(
        browser, "?csv=https://stolaf.dev/course-data/terms/20241.csv"
    )
    assert [el.inner_text() for el in page.query_selector_all("h2")] == ["data"]
    page.close()


def test_load_multiple_database_urls(static_server, browser: Browser):
    page = load_page(
        browser,
        "?url=https://latest.datasette.io/fixtures.db"
        "&url=https://datasette.io/content.db"
        "&url=https://latest.datasette.io/fixtures.db",
    )
    assert [el.inner_text() for el in page.query_selector_all("h2")] == [
        "fixtures",
        "content",
        "fixtures_2",
    ]
    page.close()


def test_ref(static_server, browser: Browser):
    page = load_page(browser, "?ref=1.0a11#/-/versions")
    info = json.loads(page.text_content("pre"))
    assert info["datasette"]["version"] == "1.0a11"
    page.close()
