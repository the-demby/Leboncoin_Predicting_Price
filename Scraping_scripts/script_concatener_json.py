import os
import json

def concatenate_json_files(input_folder: str, output_file: str):
    """
    Concatène tous les fichiers JSON dans un dossier en un seul fichier JSON.
    
    Args:
        input_folder (str): Chemin du dossier contenant les fichiers JSON.
        output_file (str): Chemin du fichier JSON résultant.
    """
    all_data = []

    # Parcourir tous les fichiers dans le dossier
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):  # Vérifier l'extension des fichiers
            file_path = os.path.join(input_folder, file_name)
            print(f"Processing file: {file_path}")
            
            # Charger les données du fichier JSON
            try:
                with open(file_path, "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    if isinstance(data, list):  # Ajouter seulement si c'est une liste
                        all_data.extend(data)
                    else:
                        print(f"Skipping file {file_name} (not a list of ads).")
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    # Sauvegarder toutes les données combinées dans un fichier JSON
    with open(output_file, "w", encoding="utf-8") as output_json:
        json.dump(all_data, output_json, ensure_ascii=False, indent=4)

    print(f"All JSON files concatenated into: {output_file}")
    print(f"Total ads collected: {len(all_data)}")

# Exemple d'utilisation
if __name__ == "__main__":
    input_folder = "./Data"  # Chemin du dossier contenant les fichiers JSON
    output_file = "combined_leboncoin_ads.json"  # Nom du fichier JSON combiné
    concatenate_json_files(input_folder, output_file)
    