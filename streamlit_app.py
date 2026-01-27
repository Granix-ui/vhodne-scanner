import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import re

st.title("Vhodné uveřejnění – aktivní zakázky")

urls_text = st.text_area(
    "Zadej URL profilů zadavatelů (jedna na řádek)",
    height=200,
    value="https://www.vhodne-uverejneni.cz/profil/thermal-f-a-s\n"
          "https://www.vhodne-uverejneni.cz/profil/00254819\n"
          "https://www.vhodne-uverejneni.cz/profil/00573183?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-vresova\n"
          "https://www.vhodne-uverejneni.cz/profil/00259349\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-lomnice?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/00253936\n"
          "https://www.vhodne-uverejneni.cz/profil/00254592\n"
          "https://www.vhodne-uverejneni.cz/profil/00255050\n"
          "https://www.vhodne-uverejneni.cz/profil/witte-nejdek-spol-s-r-o?page-actual=1#page-actual\n"
          "https://www.vhodne-uverejneni.cz/profil/00255076\n"
          "https://www.vhodne-uverejneni.cz/profil/47700521"
)

if st.button("Načíst čerstvá data"):
    urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
    if not urls:
        st.error("Zadej alespoň jednu URL!")
        st.stop()

    now = datetime.now()

    with st.spinner("Načítám data..."):
        for base_url in urls:
            # Zajistit záložku aktuálních zakázek
            profile_url = base_url
            if "tabs[xenorganization_detail_orders]" not in base_url and "#page-actual" not in base_url:
                profile_url = base_url + ("?tabs[xenorganization_detail_orders]=1" if "?" not in base_url else "&tabs[xenorganization_detail_orders]=1")

            pages_to_scrape = [profile_url]

            # Detekce paginace (page-actual nebo čísla stránek)
            try:
                response = requests.get(profile_url, timeout=15)
                soup = BeautifulSoup(response.text, "lxml")
                pagination = soup.find("div", class_=re.compile(r"pagination", re.I)) or soup.find("ul", class_=re.compile(r"pagination", re.I))
                if pagination:
                    links = pagination.find_all("a", href=True)
                    max_page = 1
                    for link in links:
                        href = link["href"]
                        if "page-actual=" in href or "page=" in href:
                            try:
                                page_num = int(parse_qs(urlparse(href).query).get("page-actual", [0])[0] or parse_qs(urlparse(href).query).get("page", [0])[0])
                                max_page = max(max_page, page_num)
                            except:
                                pass
                    if max_page > 1:
                        for p in range(2, max_page + 1):
                            page_url = base_url + f"?page-actual={p}#page-actual"
                            pages_to_scrape.append(page_url)
            except:
                pass

            # Název zadavatele
            try:
                base_response = requests.get(base_url, timeout=15)
                base_soup = BeautifulSoup(base_response.text, "lxml")
                page_title = base_soup.title.text.strip() if base_soup.title else ""
                instance_name = page_title.split(":")[-1].split(",")[0].strip() if ":" in page_title else base_url.split("/")[-1]
            except:
                instance_name = base_url.split("/")[-1]

            active_links = []

            for page_url in pages_to_scrape:
                try:
                    response = requests.get(page_url, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "lxml")

                    # Tabulka zakázek
                    table = soup.find("table")
                    if not table:
                        continue

                    rows = table.find_all("tr")[1:]  # přeskočit hlavičku

                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) < 3:
                            continue

                        name_tag = cols[0].find("a")
                        if not name_tag:
                            continue
                        name = name_tag.text.strip()
                        link = urljoin(page_url, name_tag["href"])

                        deadline_str = cols[2].text.strip() if len(cols) > 2 else ""

                        if not deadline_str or deadline_str == "nezveřejněna":
                            continue

                        try:
                            deadline = datetime.strptime(deadline_str, "%d.%m.%Y")
                            if deadline > now:
                                active_links.append(f"[{name}]({link})")
                        except ValueError:
                            continue

                except:
                    pass

            st.markdown(f"### {instance_name}")

            if active_links:
                for link in active_links:
                    st.markdown(f"- {link}", unsafe_allow_html=True)
            else:
                st.markdown("Nic nenalezeno")
