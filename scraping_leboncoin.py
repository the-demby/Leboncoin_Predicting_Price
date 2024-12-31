import asyncio
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapflyAspError, ScrapeApiResponse
import json

def parse_search(result: ScrapeApiResponse):
    """
    Parse search result data from the script tag.
    - Localise le script contenant les données JSON dans l'HTML.
    - Extrait et filtre les colonnes utiles uniquement pour simplifier les données.
    """
    # Sélectionne le script contenant les données (balise <script id="__NEXT_DATA__">)
    next_data = result.selector.css("script[id='__NEXT_DATA__']::text").get()
    if not next_data:
        raise ValueError("Unable to find __NEXT_DATA__ script tag in the HTML.")
    
    try:
        data = json.loads(next_data)
        print(json.dumps(data, indent=4))  # Affiche toute la structure pour vérifier
        
        # Essayez d'accéder directement aux annonces dans le JSON
        ads_data = data["props"]["pageProps"].get("searchData", {}).get("ads", [])
        print(f"Parsed Ads: {ads_data}")
        
        # Retournez les annonces si elles existent
        return ads_data
    except KeyError as e:
        raise KeyError(f"KeyError: {e}. JSON structure may have changed.")

async def scrape_leboncoin(url: str, max_pages: int, api_key: str):
    """
    Scrape leboncoin.fr using Scrapfly SDK.
    - Initialise un client Scrapfly avec la clé API.
    - Scrape la première page pour initialiser les données.
    - Génère des configurations pour scraper plusieurs pages en parallèle.
    - Gère les erreurs ASP pour éviter les interruptions brutales.
    """
    scrapfly = ScrapflyClient(key=api_key)

    # Base configuration for scraping
    base_config = {
        "asp": True,  # Active le contournement des protections anti-scraping
        "country": "FR"  # Utilise un proxy basé en France
    }

    # Scrape la première page
    try:
        first_page = await scrapfly.async_scrape(ScrapeConfig(url=url, **base_config))
        all_ads = parse_search(first_page)
    except ScrapflyAspError as e:
        print(f"Failed to scrape first page: {e}")
        return []

    # Generate configurations for subsequent pages
    scrape_configs = [
        ScrapeConfig(url=f"{url}&page={page}", **base_config)
        for page in range(2, max_pages + 1)
    ]

    # Scrape additional pages concurrently
    for config in scrape_configs:
        try:
            result = await scrapfly.async_scrape(config)
            all_ads.extend(parse_search(result))
            await asyncio.sleep(2)  # Introduit un délai entre les requêtes
        except ScrapflyAspError as e:
            print(f"Error on page {config.url}: {e}. Retrying after delay...")
            await asyncio.sleep(5)  # Attend avant de réessayer
        except Exception as e:
            print(f"Unexpected error: {e}")

    return all_ads

if __name__ == "__main__":
    # URL de recherche pour la catégorie voitures sur Leboncoin
    search_url = "https://www.leboncoin.fr/c/voitures"
    
    # Clé API Scrapfly (remplacez par votre clé API valide)
    api_key = "scp-live-52627853b8cd46419ee61139c1efb153"

    # Nombre de pages à scraper
    pages_to_scrape = 50  # Limité pour réduire les risques d'erreurs

    # Exécute le scraping et sauvegarde les résultats
    ads_data = asyncio.run(scrape_leboncoin(search_url, pages_to_scrape, api_key))

    # Sauvegarde les annonces extraites dans un fichier JSON
    with open("leboncoin_ads.json", "w", encoding="utf-8") as file:
        json.dump(ads_data, file, ensure_ascii=False, indent=4)

    print(f"Scraped {len(ads_data)} ads. Data saved to 'leboncoin_ads.json'.")
