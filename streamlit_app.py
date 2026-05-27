import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

st.title("Vhodné uveřejnění – aktivní zakázky (okolí Vřesové)")

# Seznam seřazený podle vzdálenosti od Vřesové (356 01)
urls_text = st.text_area(
    "Zadej URL profilů zadavatelů (jedna na řádek) - seřazeno od nejbližších",
    height=480,
    value="https://www.vhodne-uverejneni.cz/profil/obec-vresova\n"
          "https://www.vhodne-uverejneni.cz/profil/00259349\n"          # Těšovice
          "https://www.vhodne-uverejneni.cz/profil/00254592\n"
          "https://www.vhodne-uverejneni.cz/profil/00255050\n"
          "https://www.vhodne-uverejneni.cz/profil/00253936\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-lomnice?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/thermal-f-a-s\n"     # Sokolov
          "https://www.vhodne-uverejneni.cz/profil/00254819\n"
          "https://www.vhodne-uverejneni.cz/profil/00573183?tabs[xenorganization_detail_orders]=1\n"
          "https://www.vhodne-uverejneni.cz/profil/witte-nejdek-spol-s-r-o\n"
          "https://www.vhodne-uverejneni.cz/profil/00255076\n"
          "https://www.vhodne-uverejneni.cz/profil/47700521\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-tesovice-1\n"
          "https://www.vhodne-uverejneni.cz/profil/26319438\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-lipova\n"
          "https://www.vhodne-uverejneni.cz/profil/00259250\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-cernava\n"
          "https://www.vhodne-uverejneni.cz/profil/mesto-loket\n"
          "https://www.vhodne-uverejneni.cz/profil/mesto-plesna\n"
          "https://www.vhodne-uverejneni.cz/profil/00254231\n"
          "https://www.vhodne-uverejneni.cz/profil/vodarna-sokolovsko-s-r-o\n"
          "https://www.vhodne-uverejneni.cz/profil/obec-straz-nad-ohri\n"
          "# Vzdálenější (30–50 km)\n"
          "https://www.vhodne-uverejneni.cz/profil/mesto-nova-role\n"
          "https://www.vhodne-uverejneni.cz/profil/mesto-hroznetin\n"
          "https://www.vhodne-uverejneni.cz/profil/mesto-tepla"
)

if st.button("Načíst čerstvá data"):
    urls = [u.strip() for u in urls_text.split("\n") if u.strip() and not u.strip().startswith("#")]
    if not urls:
        st.error("Zadej alespoň jednu URL!")
        st.stop()

    now = datetime.now()

    with st.spinner("Načítám aktivní zakázky..."):
        for base_url in urls:
            try:
                url = base_url
                if "tabs[xenorganization_detail_orders]" not in url:
                    separator = "?" if "?" not in url else "&"
                    url += separator + "tabs[xenorganization_detail_orders]=1"

                response = requests.get(url, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                title = soup.title.text.strip() if soup.title else base_url.split("/")[-1]
                instance_name = title.split("|")[0].split("–")[0].split("-")[0].strip()

                active_links = []

                for row in soup.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) < 3:
                        continue

                    name_tag = cols[0].find("a")
                    if not name_tag:
                        continue

                    name = name_tag.text.strip()
                    link = urljoin(url, name_tag["href"])

                    deadline_text = cols[2].text.strip() if len(cols) > 2 else ""

                    if not deadline_text or "nezveřejněna" in deadline_text.lower():
                        continue

                    try:
                        if deadline_text.lower().startswith("dnes"):
                            time_part = deadline_text.split()[-1]
                            deadline = now.replace(hour=int(time_part[:2]), minute=int(time_part[3:5]), second=0)
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
