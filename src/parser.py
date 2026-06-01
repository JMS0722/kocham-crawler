import re
from bs4 import BeautifulSoup


def parse_list_page(html: str) -> list[int]:
    """목록 페이지에서 wr_id 리스트를 추출한다."""
    soup = BeautifulSoup(html, "html.parser")
    ids = []
    for link in soup.select("a[href*='detail.php?wr_id=']"):
        match = re.search(r"wr_id=(\d+)", link["href"])
        if match:
            wr_id = int(match.group(1))
            if wr_id not in ids:
                ids.append(wr_id)
    return ids


def parse_detail_page(html: str, wr_id: int) -> dict:
    """상세 페이지에서 기업 정보를 추출한다."""
    soup = BeautifulSoup(html, "html.parser")
    data = {"wr_id": wr_id}

    field_map = {
        "Company name": "company_name",
        "General Director": "director",
        "Type of business": "business_type",
        "Tel": "tel",
        "Fax": "fax",
        "Area": "area",
        "Address": "address",
        "E-mail": "email",
        "Homepage": "homepage",
        "Number of staff": "staff",
        "Service": "service",
    }

    table = soup.select_one("#table_list table.subtable_list")
    if not table:
        return data

    for row in table.select("tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue

        header = th.get_text(strip=True)
        key = field_map.get(header)
        if not key:
            continue

        if key == "homepage":
            a_tag = td.select_one("a")
            value = a_tag["href"] if a_tag and a_tag.get("href") else td.get_text(strip=True)
        else:
            value = td.get_text(strip=True)

        # clean up whitespace
        value = re.sub(r"\s+", " ", value).strip()
        data[key] = value

    return data
