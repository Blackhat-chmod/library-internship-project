import asyncio

from rag_pipeline import (
    add_document,
    retrieve,
    build_prompt,
    generate_answer
)


documents = [
    (
        """
        The Aurora Library contains a science fiction collection
        focused on space exploration, robotics, and future technology.
        One popular book follows a crew travelling through a wormhole
        to find a new home for humanity.
        """,
        "science_fiction.txt"
    ),

    (
        """
        The library's fantasy collection includes stories about
        magic, dragons, ancient kingdoms, and young heroes.
        One story follows a young wizard studying at a magical school.
        """,
        "fantasy.txt"
    ),

    (
        """
        The technology section contains books about Python,
        software engineering, web development, databases,
        and artificial intelligence.
        """,
        "technology.txt"
    )
]


for text, source in documents:
    add_document(
        text,
        source
    )


async def run_demo():

    question = (
        "What is the capital of Japan?"
    )

    chunks, metadata = retrieve(
        question
    )

    print(
        "\nRetrieved chunks:"
    )

    for chunk in chunks:
        print(
            "\n",
            chunk.strip()
        )

    print(
        "\nSources:"
    )

    for item in metadata:
        print(
            item["source"]
        )

    prompt = build_prompt(
        question,
        chunks
    )

    answer = await generate_answer(
        prompt
    )

    print(
        "\nAnswer:"
    )

    print(answer)


asyncio.run(
    run_demo()
)