import json
import os
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from sklearn.metrics.pairwise import cosine_similarity


class ImageVectorStore:
    def __init__(self, vector_file_path="entity_vector_database.json"):
        """Initialize the vector store with a path to the JSON file."""
        self.vector_file_path = vector_file_path
        self.model = self._load_model()
        self.transform = self._get_transform()
        self.vectors = self._load_vectors()

    def _load_model(self):
        """Load a pre-trained ResNet model for image embedding."""
        model = models.resnet50(weights="IMAGENET1K_V2")
        # Remove the classification layer to get features
        model = torch.nn.Sequential(*list(model.children())[:-1])
        model.eval()
        return model

    def _get_transform(self):
        """Define image transformations for the model."""
        return transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def _load_vectors(self):
        """Load existing vectors from the JSON file if it exists."""
        if os.path.exists(self.vector_file_path):
            with open(self.vector_file_path, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Vector database json file not found at {self.vector_file_path}")

    def generate_embedding(self, image: Image.Image):
        """Generate embedding for an image."""
        try:
            image_tensor = self.transform(image).unsqueeze(0)

            with torch.no_grad():
                features = self.model(image_tensor)

            # Flatten the features and convert to numpy array
            features = features.squeeze().numpy()
            return features.tolist()  # Convert to list for JSON serialization

        except Exception as e:
            print(f"Error generating embedding")
            return None

    def find_similar(self, image: Image.Image, top_k=3):
        """Find similar images to the query image."""
        query_embedding = self.generate_embedding(image)
        if not query_embedding or not self.vectors:
            return []

        # Convert query embedding to numpy array
        query_embedding_np = np.array(query_embedding).reshape(1, -1)

        # Get all embeddings from the store
        stored_embeddings = [np.array(item["embedding"]).reshape(1, -1) for item in self.vectors]

        # Calculate similarities
        similarities = []
        for i, embedding in enumerate(stored_embeddings):
            sim = cosine_similarity(query_embedding_np, embedding)[0][0]
            similarities.append((i, sim))

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k results with their metadata
        top_results = []
        for idx, sim in similarities[:top_k]:
            result = {
                "image_path": self.vectors[idx]["path"],
                "similarity": float(sim),  # Convert numpy float to Python float
                "metadata": self.vectors[idx]["metadata"],
            }
            top_results.append(result)

        return top_results


# Example usage
if __name__ == "__main__":
    # Initialize the vector store
    store = ImageVectorStore()

    for file in os.listdir("./vector_store_test_images"):
        name = file.split(".")[0]
        image = Image.open(f"./vector_store_test_images/{file}").convert("RGB")
        similar_images = store.find_similar(image)
        print(f"most similar image for {name} is {similar_images[0]['image_path']}")
        print(f"similarity score is {similar_images[0]['similarity']}")
        print("---")
        print("\n")
