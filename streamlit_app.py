import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

st.title("Vhodné uveřejnění – aktivní zakázky")

urls_text = st.text_area(
    "Zadej URL profilů zadavatelů (jedna na řádek)",
    height=300,
    value="https://www.vhodne-uverejneni.cz/profil/thermal-f-a-s\n"
          "https://www.vhodne-uverejneni.cz/profil/00254819\n"
          "https://www.vhodne-uverejneni.cz/profil/00573183?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-vresova\n"
          "https://www.vhodne-uverejneni.cz/profil/00259349\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-lomnice?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/00253936\n"
          "https://www.vhodne-uverejneni.cz/profil/00254592\n"
          "https://www.vhodne-uverejneni.cz/profil/00255050\n"
          "https://www.vhodne-uverejneni.cz/profil/witte-nejdek-spol-s-r-o\n"
          "https://www.vhodne-uverejneni.cz/profil/00255076\n"
          "https://www.vhodne-uverejneni.cz/profil/47700521"
)

if st.button("Načíst čerstvá data"):
    urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
    if not urls:
        st.error("Zadej alespoň jednu URL!")
        st.stop()

    now = datetime.now()

    with st.spinner("Načítám aktivní zakázky..."):
        for base_url in urls:
            # Zajistíme zobrazení aktivních zakázek
            url = base_url
            if "tabs[xenorganization_detail_orders]" not in url:
                separator = "?" if "?" not in url else "&"
                url = url + separator + "tabs[xenorganization_detail_orders]=1"

            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                # Název zadavatele
                title = soup.title.text.strip() if soup.title else ""
                instance_name = title.split("|")[0].strip() if "|" in title else title.split("-")[0].strip()

                active_links = []

                # Hledání zakázek v tabulce
                for row in soup.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) < 3:
                        continue

                    name_tag = cols[0].find("a")
                    if not name_tag:
                        continue

                    name = name_tag.text.strip()
                    link = urljoin(url, name_tag["href"])

                    # Lhůta pro podání nabídek je obvykle ve 3. sloupci
                    deadline_col = cols[2].text.strip() if len(cols) > 2 else ""

                    if not deadline_col or "nezveřejněna" in deadline_col.lower():
                        continue

                    try:
                        deadline = datetime.strptime(deadline_col, "%d.%m.%Y")
                        if deadline > now:
                            active_links.append(f"[{name}]({link})")
                    except:
                        continue

                st.markdown(f"### {instance_name}")

                if active_links:
                    for link_md in active_links:
                        st.markdown(f"- {link_md}", unsafe_allow_html=True)
                else:
                    st.markdown("Nic nenalezeno")

            except Exception as e:
                st.warning(f"Chyba při načítání {base_url}")
