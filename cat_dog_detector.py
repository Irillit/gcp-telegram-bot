from PIL import Image, ImageDraw, ImageFont
from google.cloud import vision


class CatDogDetector:

    LABELS = ["Cat", "Dog", "Animal"]
    COLOURS = {"Cat": (255, 255, 255),
               "Dog": (157, 255, 138),
               "Animal": (255, 255, 130)}

    FONT = "open_sans.ttf"

    def get_image(self, filename):
        with open(filename, 'rb') as user_image:
            content = user_image.read()
            image = vision.Image(content=content)
        return image

    def detect(self, filename) -> list:
        image = self.get_image(filename)
        client = vision.ImageAnnotatorClient()
        objects = client.object_localization(image=image).localized_object_annotations
        result = []
        if len(objects) > 0:
            with Image.open(filename) as im:
                size = im.size
                draw = ImageDraw.Draw(im)
                font = ImageFont.truetype(self.FONT, 18)
                for object_ in objects:
                    if object_.name in self.LABELS:
                        vertexes = []
                        result.append((object_.name, object_.score))
                        for vertex in object_.bounding_poly.normalized_vertices:
                            vertexes.append((size[0] * vertex.x, size[1] * vertex.y))
                        draw.rectangle((vertexes[0], vertexes[2]), outline=self.COLOURS[object_.name])
                        draw.text(vertexes[0],
                                  f"{object_.name} {round(object_.score, 3)}",
                                  self.COLOURS[object_.name],
                                  font=font)
                im.save(filename)
        return result
