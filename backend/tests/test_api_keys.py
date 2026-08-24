import asyncio
import os
import sys

# Append backend to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Temporarily override environment variables for the test
os.environ["GEMINI_API_KEY"] = "AIzaSyA3wKcguviBN0cuzLTrU7xM2MNwTxRiIXY"
os.environ["GEMINI_MODEL"] = "gemini-3.6-flash"
os.environ["HF_TOKEN"] = "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"
os.environ["HF_MODEL"] = "mistralai/Mistral-7B-Instruct-v0.2"

from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.huggingface_provider import HuggingFaceProvider

async def main():
    print("Testing Gemini Provider...")
    gemini = GeminiProvider()
    try:
        q_gemini = await gemini.generate_questions("technical", "easy", 1, "Google")
        print("✅ Gemini successfully generated questions:")
        print(q_gemini)
    except Exception as e:
        print("❌ Gemini failed:", e)

    print("\n----------------------------------\n")

    print("Testing HuggingFace Provider...")
    hf = HuggingFaceProvider()
    try:
        q_hf = await hf.generate_questions("behavioral", "medium", 1, "Amazon")
        print("✅ HuggingFace successfully generated questions:")
        print(q_hf)
    except Exception as e:
        print("❌ HuggingFace failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
