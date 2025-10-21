import cv2
import numpy as np
import pytesseract
import os

def getTextFromImage(image_path, gamma=1, lang='eng'):
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image non trouvée: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")

        look_up_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                                  for i in np.arange(0, 256)]).astype("uint8")
        contrasted_image = cv2.LUT(image, look_up_table)

        temp_image_path = "image_contrastee.jpg"
        cv2.imwrite(temp_image_path, contrasted_image)

        text = pytesseract.image_to_string(temp_image_path, lang=lang)

        os.remove(temp_image_path)

        return text.strip()

    except FileNotFoundError as e:
        print(f"Erreur: {e}")
        return None
    except ValueError as e:
        print(f"Erreur: {e}")
        return None
    except pytesseract.TesseractError as e:
        print(f"Erreur Tesseract: {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return None