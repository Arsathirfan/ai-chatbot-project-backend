import os
from dotenv import load_dotenv

from rag import generate_answer

load_dotenv()

# ==========================================
# 🔥 MAIN TEST
if __name__ == "__main__":

    # 🔹 Step 1: Insert data (run once)
    # docs = [
    #     "Photosynthesis is how plants make food using sunlight.",
    #     "Plants convert sunlight into chemical energy.",
    #     "Java is a backend programming language.",
    #     "The human heart pumps blood.",
    #     "Flutter is used for mobile app development.",
    #     "Python is used in AI and machine learning."
    # ]
    #
    # insert_documents(docs)
    #
    # print("\n========================")
    # print("🤖 RAG CHAT TEST")
    # print("========================\n")

    while True:
        query = input("You: ")

        if query.lower() in ["exit", "quit"]:
            break

        answer = generate_answer(query)

        print("\nBot:", answer)
        print("\n----------------------\n")