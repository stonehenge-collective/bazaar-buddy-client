import unittest
import numpy as np
import cv2
from pathlib import Path
from fight_processor_worker import FightProcessorWorker
from configuration import Configuration
from logging import getLogger

class DummyLogger:
    def debug(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass

class TestCompareImagesWithImages(unittest.TestCase):
    def setUp(self):
        self.cfg = Configuration()
        self.logger = DummyLogger()
        self.worker = FightProcessorWorker("test_worker", self.cfg, self.logger)

        self.board_path = Path("Full_Screen.png")
        assert self.board_path.exists(), f"Missing board image: {self.board_path}"
        self.board_img = self.worker._load_image(str(self.board_path))
        self.board_img, _ = self.worker._get_center_vertical_strip(self.board_img)

    def run_template_test(self, template_name: str, item_size, threshold: float = 0.6, should_match: bool = True):
        path = Path(f"item_images/{item_size}/{template_name}.png")
        assert path.exists(), f"Missing template image: {path}"

        template_img = self.worker._load_image(str(path))
        template_img = self.worker._resize_image(
            template_img,
            item_size,
            self.worker._get_image_dimensions(self.board_img)
        )

        matches = self.worker.compare_images(self.board_img.copy(), template_img, threshold=threshold)
        self.assertIsInstance(matches, list)

        if should_match:
            self.assertGreater(len(matches), 0, f"No matches found for {template_name}")
            for match in matches:
                rect = match['rect']
                score = match['score']
                print(f"[{template_name}] Match at {rect}, score={score:.3f}")
                self.assertGreaterEqual(score, threshold)
        else:
            self.assertEqual(len(matches), 0, f"Unexpected match found for {template_name}")

    def test_piranha_match(self):
        self.run_template_test("Piranha", "Small", should_match=True)  # Expected to match

    def test_nanobot_no_match(self):
        self.run_template_test("Nanobot", "Small", should_match=False)  # Expected to not match


if __name__ == "__main__":
    unittest.main()