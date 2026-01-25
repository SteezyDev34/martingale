from PIL import Image
from pylibdmtx import encode

data = "Nom: Dupont|Date: 2025-11-11|Montant: 250.00€|SIGN:abc123"

encoded = encode(data.encode('utf-8'))

img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
img.save("2ddoc_datamatrix.png")

print("✅ Datamatrix 2D-Doc généré : 2ddoc_datamatrix.png")
