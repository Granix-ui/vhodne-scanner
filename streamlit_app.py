import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin

st.title("Vhodné uveřejnění – aktivní zakázky")

urls_text = st.text_area(
    "Zadej URL profilů zadavatelů (jedna na řádek)",
    height=320,
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

    with st.spinner("Načítám aktivní zakázky z Aktuálního uveřejnění..."):
        for base_url in urls:
            try:
                # Přechod na záložku Aktuální uveřejnění
                url = base_url
                if "tabs[xenorganization_detail_orders]" not in url:
                    separator = "?" if "?" not in url else "&"
                    url += separator + "tabs[xenorganization_detail_orders]=1"

                response = requests.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                # Název zadavatele
                title = soup.title.text.strip() if soup.title else base_url.split("/")[-1]
                instance_name = title.split("|")[0].split("–")[0].split("-")[0].strip()

                active_links = []

                # Hledání v tabulce
                for row in soup.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) < 3:
                        continue

                    name_tag = cols[0].find("a")
                    if not name_tag:
                        continue

                    name = name_tag.text.strip()
                    link = urljoin(url, name_tag["href"])

                    # Lhůta pro nabídky (3. sloupec)
                    deadline_text = cols[2].text.strip()

                    if not deadline_text or "nezveřejněna" in deadline_text.lower():
                        continue

                    try:
                        # Podpora "Dnes 15:00:00"
                        if deadline_text.lower().startswith("dnes"):
                            time_str = deadline_text.split()[-1]
                            deadline = now.replace(hour=int(time_str[:2]), minute=int(time_str[3:5]), second=0)
                        else:
                            deadline = datetime.strptime(deadline_text, "%d.%m.%Y")
                        
                        if deadline > now:
                            active_links.append(f"[{name}]({link}) — lhůta {deadline_text}")
                    except:
                        continue

                st.markdown(f"### {instance_name}")

                if active_links:
                    for link_md in active_links:
                        st.markdown(f"- {link_md}", unsafe_allow_html=True)
                else:
                    st.markdown("Nic nenalezeno")

            except Exception:
                st.warning(f"Nepodařilo se načíst {base_url}")
