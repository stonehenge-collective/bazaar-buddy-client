import os
import json
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from tqdm import tqdm


def load_model():
    """Load a pre-trained ResNet model for image embedding."""
    model = models.resnet50(weights="IMAGENET1K_V2")
    # Remove the classification layer to get features
    model = torch.nn.Sequential(*list(model.children())[:-1])
    model.eval()
    return model


def get_transform():
    """Define image transformations for the model."""
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def generate_embedding(model, transform, image_path):
    """Generate embedding for an image."""
    try:
        image = Image.open(image_path).convert("RGB")
        image_tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            features = model(image_tensor)

        # Flatten the features and convert to numpy array
        features = features.squeeze().numpy()
        return features.tolist()  # Convert to list for JSON serialization

    except Exception as e:
        print(f"Error generating embedding for {image_path}: {e}")
        return None


def create_database(image_dir, output_file):
    """Create a database of image embeddings."""
    model = load_model()
    transform = get_transform()

    # Get list of image files
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    database = []

    # Process each image
    for image_file in tqdm(image_files, desc="Processing images"):
        image_path = os.path.join(image_dir, image_file)

        # Extract item name from filename (remove extension)
        item_name = os.path.splitext(image_file)[0].replace("_", " ")

        # Generate embedding
        embedding = generate_embedding(model, transform, image_path)

        if embedding:
            # Create item entry
            item_data = {
                "path": image_path,
                "embedding": embedding,
                "metadata": {"name": item_name, "filename": image_file},
            }

            database.append(item_data)

    # Save to JSON file
    with open(output_file, "w") as f:
        json.dump(database, f, indent=2)

    print(f"Created database with {len(database)} items in {output_file}")


if __name__ == "__main__":
    import sys

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_dir = os.path.join(parent_dir, "client-data", "item_images")
    output_file = os.path.join(parent_dir, "entity_vector_database.json")
    create_database(image_dir, output_file)
