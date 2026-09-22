import chromadb


chroma_client = chromadb.Client()

collection = chroma_client.create_collection(
    name="books_demo"
)


collection.add(
    documents=[
        "A young wizard attends a magic school and fights a dark lord.",
        "A crew travels through a wormhole to save humanity from a dying Earth.",
        "Two feuding families in 19th century England navigate love and marriage.",
        "A detective investigates a mysterious murder in a quiet town.",
        "A beginner learns Python programming and software development."
    ],
    metadatas=[
        {
            "source": "book_1.txt",
            "category": "Fantasy"
        },
        {
            "source": "book_2.txt",
            "category": "Science Fiction"
        },
        {
            "source": "book_3.txt",
            "category": "Romance"
        },
        {
            "source": "book_4.txt",
            "category": "Mystery"
        },
        {
            "source": "book_5.txt",
            "category": "Technology"
        }
    ],
    ids=[
        "book_1",
        "book_2",
        "book_3",
        "book_4",
        "book_5"
    ]
)


print("=== General semantic search ===")

results = collection.query(
    query_texts=[
        "a space journey story"
    ],
    n_results=2
)

print(
    "Documents:",
    results["documents"]
)

print(
    "Metadata:",
    results["metadatas"]
)


print(
    "\n=== Metadata filtered search ==="
)

filtered_results = collection.query(
    query_texts=[
        "magic and adventure"
    ],
    n_results=2,
    where={
        "category": "Fantasy"
    }
)

print(
    "Documents:",
    filtered_results["documents"]
)

print(
    "Metadata:",
    filtered_results["metadatas"]
)