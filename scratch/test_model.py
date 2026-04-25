from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded successfully without torchvision")
except Exception as e:
    print(f"Error loading model: {e}")
