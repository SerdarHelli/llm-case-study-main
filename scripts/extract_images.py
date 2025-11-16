#!/usr/bin/env python3

import os
import json
import pymupdf
import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageExtractor:
    def __init__(self, output_dir: str = "data/images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract images from PDF and save them."""
        logger.info(f"Extracting images from {pdf_path}")
        
        doc = pymupdf.open(pdf_path)
        images_info = []
        image_count = 0
        
        for page_num, page in enumerate(doc):
            logger.info(f"Processing page {page_num + 1}/{len(doc)}")
            
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = pymupdf.Pixmap(doc, xref)
                    
                    output_path = os.path.join(
                        self.output_dir,
                        f"page_{page_num + 1}_image_{img_index + 1}.png"
                    )
                    
                    if pix.n - pix.alpha < 4:
                        pix.save(output_path)
                    else:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                        pix.save(output_path)
                    
                    images_info.append({
                        "page": page_num + 1,
                        "image_index": img_index + 1,
                        "file_path": output_path,
                        "description": ""
                    })
                    
                    image_count += 1
                    logger.info(f"Saved image: {output_path}")
                    
                except Exception as e:
                    logger.error(f"Error extracting image on page {page_num + 1}: {e}")
        
        doc.close()
        logger.info(f"Extracted {image_count} images in total")
        return images_info
    
    def save_image_metadata(self, images_info: List[Dict], 
                           output_file: str = "data/images_metadata.json"):
        """Save image metadata."""
        logger.info(f"Saving image metadata to {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(images_info, f, indent=2)
        
        logger.info("Metadata saved")

def main():
    pdf_path = "data/dr_voss_diary.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found at {pdf_path}")
        return
    
    extractor = ImageExtractor()
    images_info = extractor.extract_images_from_pdf(pdf_path)
    extractor.save_image_metadata(images_info)
    
    logger.info(f"Image extraction complete! Found {len(images_info)} images.")

if __name__ == "__main__":
    main()
