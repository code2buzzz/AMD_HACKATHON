import requests
from langchain_ollama import ChatOllama


# -----------------------------
# OPTION 1: Direct API test
# -----------------------------
def test_raw_ollama():
    print("\n🔵 Testing raw Ollama API...\n")

    url = "http://localhost:11434/api/chat"

    payload = {
        "model": "llama3:70b",
        "stream": False,
        "messages": [{"role": "user", "content": "Explain fraud detection in 2 lines"}],
    }

    r = requests.post(url, json=payload)

    if r.status_code == 200:
        print("✅ Raw API Response:\n")
        print(r.json()["message"]["content"])
    else:
        print("❌ Error:", r.text)


# -----------------------------
# OPTION 2: LangChain test
# -----------------------------
def test_langchain_ollama():
    print("\n🟢 Testing LangChain ChatOllama...\n")

    llm = ChatOllama(
        model="llama3:70b",
        base_url="http://localhost:11434",
        temperature=0,
        num_ctx=8192,
    )

    response = llm.invoke("Explain fraud detection in banking in 2 lines")

    print("✅ LangChain Response:\n")
    print(response.content)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("\n🚀 Starting Ollama LLM tests...\n")

    test_raw_ollama()
    test_langchain_ollama()

    print("\n🎯 Done!\n")
