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
    value="https://www.vhodne-uverejneni.cz/profil/obec-vresova\n"          # Vřesová
          "https://www.vhodne-uverejneni.cz/profil/obec-tesovice\n"          # Těšovice
          "https://www.vhodne-uverejneni.cz/profil/obec-lomnice\n"          # Lomnice
          "https://www.vhodne-uverejneni.cz/profil/00254819\n"          # Nová Role
          "https://www.vhodne-uverejneni.cz/profil/mesto-nova-role\n"          # Nová Role
          "https://www.vhodne-uverejneni.cz/profil/00259349\n"          # Chodov
          "https://www.vhodne-uverejneni.cz/profil/00573183?\n"          # Božičany
          "https://www.vhodne-uverejneni.cz/profil/00259250\n"          # Březová
          "https://www.vhodne-uverejneni.cz/profil/mesto-loket\n"          # Loket
          "https://www.vhodne-uverejneni.cz/profil/00254231\n"          # Skalná
          "https://www.vhodne-uverejneni.cz/profil/26319438\n"          # Chodovské TS
          "https://www.vhodne-uverejneni.cz/profil/thermal-f-a-s\n"          # Thermal
          "https://www.vhodne-uverejneni.cz/profil/vodarna-sokolovsko-s-r-o\n"          # Vod.Sokolov
          "https://www.vhodne-uverejneni.cz/profil/47700521\n"          # VH západní čechy
          "https://www.vhodne-uverejneni.cz/profil/witte-nejdek-spol-s-r-o\n"          # Witte Nejdek
          "https://www.vhodne-uverejneni.cz/profil/obec-lipova\n"          # Lipová
          "https://www.vhodne-uverejneni.cz/profil/obec-cernava\n"          # Černava
          "https://www.vhodne-uverejneni.cz/profil/mesto-plesna\n"          # Plesná
          "https://www.vhodne-uverejneni.cz/profil/mesto-hroznetin\n"          # Hroznětín
          "https://www.vhodne-uverejneni.cz/profil/00254592\n"          # Hroznětín
          "https://www.vhodne-uverejneni.cz/profil/00255050\n"          # Teplá
          "https://www.vhodne-uverejneni.cz/profil/mesto-tepla"          # Teplá
          "https://www.vhodne-uverejneni.cz/profil/00253936\n"          # Fr.Lázně
          "https://www.vhodne-uverejneni.cz/profil/00255076\n"          # Toužim
          "https://www.vhodne-uverejneni.cz/profil/obec-straz-nad-ohri\n"          # Stráž nad Ohří
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
