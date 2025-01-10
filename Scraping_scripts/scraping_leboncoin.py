import asyncio
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapflyAspError, ScrapeApiResponse
import json

# Fonction pour analyser les résultats de recherche
def parse_search(result: ScrapeApiResponse):
    """
    Extrait et analyse les données JSON des annonces contenues dans une balise <script> spécifique.
    """
    # Sélectionne le script contenant les données JSON
    next_data = result.selector.css("script[id='__NEXT_DATA__']::text").get()
    if not next_data:
        raise ValueError("Unable to find __NEXT_DATA__ script tag in the HTML.")
    
    try:
        # Parse le JSON pour récupérer les annonces
        data = json.loads(next_data)
        print(json.dumps(data, indent=4))  # Affiche la structure JSON pour vérification
        
        # Accède aux annonces dans la structure JSON
        ads_data = data["props"]["pageProps"].get("searchData", {}).get("ads", [])
        print(f"Parsed Ads: {ads_data}")
        
        return ads_data  # Retourne les annonces extraites
    except KeyError as e:
        raise KeyError(f"KeyError: {e}. JSON structure may have changed.")

# Fonction principale pour effectuer le scraping sur plusieurs pages
async def scrape_leboncoin(url: str, max_pages: int, api_key: str):
    """
    Scrape Leboncoin.fr en utilisant Scrapfly SDK.
    - Contourne les protections anti-bot.
    - Scrape plusieurs pages en parallèle.
    """
    # Initialisation du client Scrapfly avec la clé API
    scrapfly = ScrapflyClient(key=api_key)

    # Configuration de base pour le scraping
    base_config = {
        "asp": True,  # Active la protection anti-bot
        "country": "FR"  # Utilise un proxy basé en France
    }

    # Liste pour stocker toutes les annonces
    all_ads = []

    try:
        # Scrape la première page
        first_page = await scrapfly.async_scrape(ScrapeConfig(url=url, **base_config))
        all_ads.extend(parse_search(first_page))
    except ScrapflyAspError as e:
        print(f"Failed to scrape first page: {e}")
        return []

    # Générer des configurations pour les pages suivantes
    scrape_configs = [
        ScrapeConfig(url=f"{url}/p-{page}", **base_config)
        for page in range(2, max_pages + 1)
    ]

    # Scraper les pages supplémentaires
    for config in scrape_configs:
        try:
            result = await scrapfly.async_scrape(config)
            all_ads.extend(parse_search(result))  # Ajoute les annonces récupérées
            await asyncio.sleep(2)  # Pause pour éviter la détection de bot
        except ScrapflyAspError as e:
            print(f"Error on page {config.url}: {e}. Retrying after delay...")
            await asyncio.sleep(5)  # Pause supplémentaire en cas d'erreur
        except Exception as e:
            print(f"Unexpected error: {e}")

    return all_ads

if __name__ == "__main__":
    # URL de recherche pour la catégorie voitures sur Leboncoin
    search_url = "https://www.leboncoin.fr/c/voitures"
    
    # Clé API Scrapfly (remplacez par votre clé API valide)
    api_key = "votre_clé_API_scrapfly"

    # Nombre de pages à scraper
    pages_to_scrape = 10  # Par exemple, 10 pages

    # Exécute le scraping et sauvegarde les résultats
    ads_data = asyncio.run(scrape_leboncoin(search_url, pages_to_scrape, api_key))

    # Sauvegarde les annonces extraites dans un fichier JSON
    with open("leboncoin_ads.json", "w", encoding="utf-8") as file:
        json.dump(ads_data, file, ensure_ascii=False, indent=4)

    print(f"Scraped {len(ads_data)} ads. Data saved to 'leboncoin_ads.json'.")