import chromadb

def list_all_collections(persistence_path):
    # Initialize the Chroma client with the specified persistence path
    client = chromadb.PersistentClient(path=persistence_path)

    # List all collections in the Chroma DB
    collections = client.list_collections()
    return  collections


if __name__ == "__main__":
    # Define the path to your Chroma DB
    persistence_path = "./vectordb"

    # Get the list of all collection names
    collections = list_all_collections(persistence_path)

    # Print the list of collections
    if collections:
        print("List of all collections in Chroma DB:")
        for collection_name in collections:
            print(f"- {collection_name}")
    else:
        print("No collections found in the Chroma DB.")
