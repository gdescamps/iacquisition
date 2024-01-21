import pandas as pd
import numpy as np
import json
from PIL import Image
import os
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
import re

from api.utils import *
from ocr.preprocessing import *


def remove_greater_than_90_percent(bounding_boxes, image_area):
    to_remove = set()
    for i in range(len(bounding_boxes)):
        width = bounding_boxes[i][1][0] - bounding_boxes[i][0][0]
        height = bounding_boxes[i][1][1] - bounding_boxes[i][0][1]
        if width * height > 0.95 * image_area:
            to_remove.add(i)
    return [box for i, box in enumerate(bounding_boxes) if i not in to_remove]


def associate_new_region(bounding_boxes, image_shape):
    ## Si la page ne contient qu'une seule région.
    if len(bounding_boxes) == 1:
        x1, y1, x1b, y1b = (
            bounding_boxes[0][0][0],
            bounding_boxes[0][0][1],
            bounding_boxes[0][1][0],
            bounding_boxes[0][1][1],
        )
        ## Si la région remplit 90% ou plus de l'aire de la page.
        if (y1b - y1) * (x1b - x1) > image_shape[1] * image_shape[0] * 0.90:
            return bounding_boxes
        else:
            ## Si la région prend plus de 70% de la hauteur de la page.
            if (y1b - y1) > image_shape[0] * 0.7:
                ## La région est sur la droite
                if x1 > 0.4 * image_shape[1]:
                    bounding_boxes.append(
                        ((0, 0), (0.4 * image_shape[1], image_shape[0]))
                    )
                    return bounding_boxes
                ## La région est sur la gauche
                elif x1b < 0.6 * image_shape[1]:
                    bounding_boxes.append(
                        ((0.6 * image_shape[1], 0), (image_shape[1], image_shape[0]))
                    )
                    return bounding_boxes
                else:
                    return bounding_boxes

    ## Si la page contient plusieurs régions. Alors la fonction renvoie l'entrée.
    else:
        return bounding_boxes


def is_inside_or_overlaps_60_percent(box1, box2):
    """
    Check if box1 is inside or overlaps 60% or more with box2 for the format ((x1, y1), (x2, y2)).
    """
    x1, y1, x1b, y1b = box1[0][0], box1[0][1], box1[1][0], box1[1][1]
    x2, y2, x2b, y2b = box2[0][0], box2[0][1], box2[1][0], box2[1][1]

    # Calculate intersection coordinates
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1b, x2b)
    y_bottom = min(y1b, y2b)

    # Check if there is no overlap
    if x_right < x_left or y_bottom < y_top:
        return False

    # Calculate areas
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (x1b - x1) * (y1b - y1)

    # Check if box1 is inside box2 or overlaps 60% or more
    return intersection_area >= box1_area * 0.6


def remove_boxes(bounding_boxes):
    """
    Remove bounding boxes that are inside or 60% inside other bounding boxes.
    Bounding boxes are in the format ((x1, y1), (x2, y2)).
    """
    to_remove = set()

    for i in range(len(bounding_boxes)):
        for j in range(len(bounding_boxes)):
            if i != j and is_inside_or_overlaps_60_percent(
                bounding_boxes[i], bounding_boxes[j]
            ):
                to_remove.add(i)

    # Create a new list excluding the boxes to be removed
    return [box for i, box in enumerate(bounding_boxes) if i not in to_remove]


class CVDocument:
    def __init__(self):
        self.id = None
        self.nb_pages = None
        self.images = {}
        self.n_clusters = {}
        self.blocks = {}
        self.cluster_blocks = {}
        self.region_blocks = {}
        self.region_bounding_box = {}
        self.text = {}

    def plot_with_blocks(self, with_clusters=False):
        colors = {
            1: {"red": (255, 0, 0)},
            2: {"green": (0, 255, 0)},
            3: {"blue": (0, 0, 255)},
            4: {"violet": (238, 130, 238)},
            5: {"yellow": (255, 255, 0)},
        }
        if with_clusters:
            if self.n_clusters == {}:
                print("You must first assign clusters to the blocks in the document")
                return None
            else:
                for key, image in self.images.items():
                    im2 = image.copy()
                    for block_ in self.blocks[key].blocks:
                        cluster = block_.cluster
                        rect = cv2.rectangle(
                            im2,
                            (block_.x1, block_.y1),
                            (block_.x2, block_.y2),
                            list(colors[cluster].values())[0],
                            4,
                        )
                    plt.imshow(np.asarray(im2))
                    plt.show()
        else:
            for key, image in self.images.items():
                im2 = image.copy()
                for block_ in self.blocks[key].blocks:
                    rect = cv2.rectangle(
                        im2,
                        (block_.x1, block_.y1),
                        (block_.x2, block_.y2),
                        (0, 255, 0),
                        4,
                    )
                plt.imshow(np.asarray(im2))
                plt.show()
        return None

    def plot_region(self, save: bool = False, plot: bool = False):
        colors = {
            1: {"red": (255, 0, 0)},
            2: {"green": (0, 255, 0)},
            3: {"blue": (0, 0, 255)},
            4: {"violet": (238, 130, 238)},
            5: {"yellow": (255, 255, 0)},
        }
        for key, image in self.images.items():
            im2 = image.copy()
            for i, __ in enumerate(self.region_bounding_box[key]):
                rect = cv2.rectangle(
                    im2,
                    (int(__[0][0]), int(__[0][1])),
                    (int(__[1][0]), int(__[1][1])),
                    list(colors[i + 1].values())[0],
                    6,
                )
            if plot:
                plt.imshow(np.asarray(im2))
                plt.show()
            else:
                pass

            if save:
                # Create a new folder
                main_path = os.getcwd()
                output_path = os.path.join(main_path, "data/Preprocessing/CV")
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                else:
                    pass

                output_path = os.path.join(main_path, "data/Preprocessing/CV", self.id)
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                else:
                    pass
                Image.fromarray(np.asarray(im2)).save(
                    os.path.join(output_path, "{}.jpg".format(key))
                )

    def PreOCRProcessing(self):
        for key, image in self.images.items():
            contours = block_segmentation(image_numpy=image, plot=False)

            doc_blocks = DocumentBlocks(
                contours=contours, image_shape=(image.shape[0], image.shape[1])
            )
            self.blocks[key] = doc_blocks

            liste_id_to_remove = self.blocks[key].return_list_to_remove()

            self.blocks[key].remove_block(liste_id_to_remove)

            self.get_cluster_blocks()

            __ = []
            for cluster_id in range(1, self.n_clusters[key] + 1):
                __.append(
                    self.blocks[key].get_blocks_coordinates_per_cluster(cluster_id)
                )

            self.region_bounding_box[key] = compute_smallest_boundingbox(__)
            self.region_bounding_box[key] = remove_greater_than_90_percent(
                self.region_bounding_box[key],
                image_area=self.images[key].shape[0] * self.images[key].shape[1],
            )
            self.region_bounding_box[key] = remove_boxes(self.region_bounding_box[key])
            self.region_bounding_box[key] = associate_new_region(
                bounding_boxes=self.region_bounding_box[key],
                image_shape=(self.images[key].shape[0], self.images[key].shape[1]),
            )
        return None

    def remove_images(self):
        self.images = {}

    def ocr(self, ocr_engine):
        if ocr_engine == "tesseract":
            for key, image in self.images.items():
                self.text[key] = []
                image_ = Image.fromarray(image)
                try:
                    for bb_ in self.region_bounding_box[key]:
                        cropped_image = image_.crop(
                            (int(bb_[0][0]), int(bb_[0][1]), int(bb_[1][0]), int(bb_[1][1]))
                        )
                        extracted_text = pytesseract.image_to_string(
                            cropped_image, config="--psm 4"
                        )
                        self.text[key].append(extracted_text)
                except TypeError:
                    extracted_text = pytesseract.image_to_string(image_)
                    self.text[key].append(extracted_text)                   
        else:
            pass
        return None

    def get_cluster_blocks(self):
        for key, page_blocks in self.blocks.items():
            coordinates_middlepoint = {}
            for __ in page_blocks.blocks:
                coordinates_middlepoint[__.id] = __.get_middle(axis=0)
            clusters = compute_classification_hierarchical(
                coordinates_middlepoint, min=0, max=self.images[key].shape[1]
            )
            self.n_clusters[key] = len(set(clusters))
            for id, cluster_id in enumerate(clusters):
                page_blocks.get_block(id).AssignClusterBlock(cluster_id)
