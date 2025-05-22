import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from worker_framework import Worker
from configuration import Configuration
from logging import Logger
import cv2 , threading
import numpy as np
from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from operator import itemgetter
import concurrent.futures

class FightProcessorWorker(Worker):

    fight_details = pyqtSignal(object)

    def __init__(
        self,
        name: str,
        configuration: Configuration,
        logger: Logger,
        item_images_path: str = "item_images"
    ) -> None:
        super().__init__(name, logger)
        self._configuration = configuration
        self._logger = logger
        self.ITEM_IMAGES_PATH = item_images_path
        self.sizes = ["Small", "Medium", "Large"]

    def compare_images(self, board_image, image, threshold = .67):
        if board_image is None:
            raise ValueError("board_image is None. Make sure the image was loaded correctly.")
        if image is None:
            raise ValueError("image is None. Make sure the template image was loaded correctly.")
        if image.shape[0] > board_image.shape[0] or image.shape[1] > board_image.shape[1]:
            raise ValueError("The template image is larger than the board image.")
        
        self._logger.debug(f"[{threading.current_thread().name}] Comparing Image to Board (conf>=%d)", threshold)

        
        result = cv2.matchTemplate(board_image, image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        w = image.shape[1]
        h = image.shape[0]


        yloc, xloc = np.where(result >= threshold)
        rectangles = []
        rectangle_scores = []
        
        for (x, y) in zip(xloc, yloc):
            score = result[y, x]
            rect = [int(x), int(y), int(w), int(h)]
            rectangles.append(rect)
            rectangles.append(rect.copy())  # Duplicate for grouping
            rectangle_scores.append(score)
        
        # Group rectangles (using only coordinates)
        grouped_rects, _ = cv2.groupRectangles(rectangles, 1, .2)
        
        # For each grouped rectangle, find the maximum score
        final_results = []
        for (x, y, w, h) in grouped_rects:
            # Find all original rectangles that overlap with this grouped rectangle
            max_score = 0
            for i, (rx, ry, rw, rh) in enumerate(rectangles[::2]):  # Skip duplicates
                if (abs(x - rx) < w and abs(y - ry) < h):
                    if rectangle_scores[i] > max_score:
                        max_score = rectangle_scores[i]
            
            # Draw rectangle (optional)
            cv2.rectangle(board_image, (x, y), (x+w, y+h), (0, 255, 255), 2)
            
            # Store rectangle with its MAX score
            final_results.append({
                'rect': (x, y, w, h),
                'score': max_score
            })
        return final_results

    def detect_items_on_board(self, board_img):
        detected_items = []
        roi, offset = self._get_center_vertical_strip(board_img)
        for size in self.sizes:
            folder_path = os.path.join(self.ITEM_IMAGES_PATH, size)
            if not os.path.exists(folder_path):
                continue  # Skip if folder doesn't exist
            detected = self.process_folder(folder_path, size, roi)
            detected_items.extend(detected)
        self._display_image(roi)
        detected_items = self._sort_items(detected_items, roi.shape[0])

        if detected_items:
            with open("detected_items.json", "w") as f:
                json.dump(detected_items, f, indent=2)
            self.fight_details.emit(detected_items)

    def process_folder(self, folder_path: str, size: str, board_img: np.ndarray) -> list:
        """Process all images in a folder using threads and combine results"""
        self._logger.debug(f"Starting to process folder: {folder_path} with size: {size}")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all image processing tasks
            futures = []
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    self._logger.debug(f"Submitting image for processing: {file_path}")
                    futures.append(executor.submit(self.process_image, file_path, size, board_img))
            
            # Collect results as they complete
            all_detected = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    detected_items = future.result()
                    all_detected.extend(detected_items)
                except Exception as e:
                    self._logger.error("Error processing image in thread", exc_info=e)
        
        
        self._logger.info(f"Completed processing of folder '{folder_path}'. Total items detected: {len(all_detected)}")
        return all_detected

    def process_image(self, file_path: str, size: str, board_img: np.ndarray) -> list:
        """Process a single item image and return detected items"""
        self._logger.debug(f"Loading image: {file_path}")
        img = self._load_image(file_path)
        img = self._resize_image(img, size, self._get_image_dimensions(board_img))
        if img is None:
            self._logger.error(f"Failed to load image: {file_path} (file may be corrupt or not a valid image)")
            return []
        
        items = self.compare_images(board_img, img)
        detected = []
        if items:
            for item in items:
                detected.append({
                    "name": self._extract_file_string(file_path),
                    "x_coord": int(item['rect'][0]),
                    "y_coord": int(item['rect'][1]),
                    "score": float(item['score'])
                })
        return detected

    # -------------------------- internal utilities ----------------------- #

    def _sort_items(self, items, board_height):
        for item in items:
            item["board"] = "your_board" if item["y_coord"] > board_height / 2 else "enemies_board"

        your_board_items = [item for item in items if item["board"] == "your_board"]
        enemy_board_items = [item for item in items if item["board"] == "enemies_board"]

        # Sort by x-coordinate and assign positions
        for board_items in [your_board_items, enemy_board_items]:
            board_items.sort(key=itemgetter("x_coord"))
            for idx, item in enumerate(board_items, start=1):
                item["position"] = idx
        
        items = your_board_items + enemy_board_items
        return items
    
    def _extract_file_string(self, file_path):
        filename = os.path.basename(file_path)             
        name = os.path.splitext(filename)[0] 
        pretty_name = name.replace('_', ' ') 
        return pretty_name
    
    # -------------------------- image manipulation ----------------------- #

    def _load_image(self, imagePath) -> np.ndarray:
        image = cv2.imread(imagePath, cv2.IMREAD_COLOR)
        if image is None:
            self._logger.error(f"Failed to load image: {imagePath}")
            raise ValueError(f"Failed to load image: {imagePath}")
        return image
    
    def _resize_image(self, image, image_size, board_dimensions) -> np.ndarray:
        # Target dimensions (width, height)
        if image_size == "Medium":
            h = int(board_dimensions[0]  * .34)
            w = int(board_dimensions[0] * .34)
        elif image_size == "Small":
            h = int(board_dimensions[0] * .342)
            w = int(board_dimensions[0] * .162)
        elif image_size == "Large":
            h = int(board_dimensions[0] * .34)
            w = int(board_dimensions[0] * .54)
        # Resize
        resized = cv2.resize(image, (w,h), interpolation=cv2.INTER_AREA)
        return resized
    
    def _display_image(self, image, imageName="image"): 
        cv2.imshow(imageName, image)
        cv2.waitKey()
        cv2.destroyAllWindows()

    def _get_image_dimensions(self, image):
        return image.shape[:2]
    
    def _get_center_vertical_strip(self, image, height_scale=0.55, width_scale=0.6):
        h, w = self._get_image_dimensions(image)
        roi_h = max(1, int(h * height_scale))  # Ensure at least 1 pixel
        roi_w = max(1, int(w * width_scale))
        
        y_start = (h - roi_h) // 2
        y_end = y_start + roi_h
        
        x_start = (w - roi_w) // 2
        x_end = x_start + roi_w

        cropped = image[y_start:y_end, x_start:x_end]
        return cropped, (x_start, y_start)
    
if __name__ == "__main__":  # testing
    from logger import logger

    cfg = Configuration()
    fight_processor = FightProcessorWorker("Fight Processor", cfg, logger)
    board = fight_processor._load_image(Path("Full_Screen.png"))
    fight_processor.detect_items_on_board(board)


