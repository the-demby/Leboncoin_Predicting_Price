import asyncio
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapflyAspError, ScrapeApiResponse
import json
from datetime import datetime

# Fonction pour analyser les résultats de recherche
def parse_search(result: ScrapeApiResponse):
    """
    Extrait et analyse les données JSON des annonces contenues dans une balise <script> spécifique.
    """
    next_data = result.selector.css("script[id='__NEXT_DATA__']::text").get()
    if not next_data:
        raise ValueError("Unable to find __NEXT_DATA__ script tag in the HTML.")
    
    try:
        data = json.loads(next_data)
        ads_data = data["props"]["pageProps"].get("searchData", {}).get("ads", [])
        return ads_data
    except KeyError as e:
        raise KeyError(f"KeyError: {e}. JSON structure may have changed.")

# Fonction principale pour effectuer le scraping sur plusieurs pages par département
async def scrape_department(department_name: str, api_key: str):
    """
    Scrape les 100 pages d'un département spécifique.
    - department_name : Nom du département formaté pour l'URL (ex. : dp_var pour Var).
    - api_key : Clé API pour Scrapfly.
    """
    base_url = f"https://www.leboncoin.fr/cl/voitures/{department_name}/p-"
    scrapfly = ScrapflyClient(key=api_key)
    base_config = {
        "asp": True,
        "country": "FR"
    }

    all_ads = []
    for page in range(1, 21):  # Limiter à 100 pages maximum
        url = f"{base_url}{page}"
        try:
            result = await scrapfly.async_scrape(ScrapeConfig(url=url, **base_config))
            ads = parse_search(result)
            if not ads:  # Arrêter si aucune annonce n'est trouvée sur cette page
                print(f"No more ads found for department {department_name} on page {page}.")
                break

            all_ads.extend(ads)
            await asyncio.sleep(2)  # Pause pour éviter la détection de bot
        except ScrapflyAspError as e:
            print(f"Error on page {page} of department {department_name}: {e}. Skipping to next page...")
            continue
        except Exception as e:
            print(f"Unexpected error on page {page} of department {department_name}: {e}")
            break

    # Sauvegarder les annonces du département dans un fichier JSON
    output_file = f"leboncoin_ads_{department_name}.json"
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(all_ads, file, ensure_ascii=False, indent=4)

    print(f"Scraped {len(all_ads)} ads for department {department_name}. Data saved to '{output_file}'.")

# Gestion des départements
async def scrape_all_departments(api_key: str):
    """
    Scraper les annonces pour tous les 95 départements français.
    - api_key : Clé API pour Scrapfly.
    """
    departments = [
        "r_23", "r_24", "r_25", "r_26" 
    ]

    for department in departments:
        print(f"Starting scraping for department: {department}...")
        await scrape_department(department, api_key)
        print(f"Finished scraping for department: {department}.")
        await asyncio.sleep(10)  # Pause entre les départements pour éviter la détection

if __name__ == "__main__":
    # Configuration principale
    api_key = "scp-live-52627853b8cd46419ee61139c1efb153"

    # Lancer le scraping pour tous les départements
    asyncio.run(scrape_all_departments(api_key))