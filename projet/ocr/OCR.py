import cv2
from shapely import box, multipoints
from uuid import uuid4
from PIL import Image, ImageFont, ImageDraw
from numpy import asarray
import os


def merge_subword(word_labels, merge_factor=6.5, pass_count=1):
    # some constants
    in_context_list = ["(", "{", "["]
    out_context_list = [")", "}", "]"]
    for pa in range(
        pass_count
    ):  # multiple pass can merge in context () words like '(YELLOW' '5)' = '(YELLOW 5)'
        restart = 0  # restart loop at this index after word_labels element removed
        while True:
            if (
                restart == len(word_labels) - 1
            ):  # while entire word_labels list is not explored
                break
            for index in range(
                restart, len(word_labels)
            ):  # loop that begin at restart index
                restart = index
                if index < len(word_labels) - 1:
                    wl = word_labels[index]  # get current word
                    wl_1 = word_labels[index + 1]  # get next word

                    # compute min distance threshold
                    text_height = max(
                        abs(wl["bb"][1] - wl["bb"][3]),
                        abs(wl_1["bb"][1] - wl_1["bb"][3]),
                    )
                    min_dist_thres = text_height / merge_factor

                    dist = abs(
                        wl_1["bb"][0] - wl["bb"][2]
                    )  # compute abs distance between current and next word
                    on_same_line = (
                        wl_1["bb"][1] < wl["bb"][3] and wl_1["bb"][3] > wl["bb"][1]
                    )  # is on same line simple rule

                    same_context = False
                    if pa > 0:  # if we are in the second pass or more
                        if any([x == wl["text"][0] for x in in_context_list]) and any(
                            [x == wl_1["text"][-1] for x in out_context_list]
                        ):  # if we are in same context ex : '(YELLOW' '5)'
                            same_context = True

                    if on_same_line and (
                        dist < min_dist_thres or same_context
                    ):  # if we are on same line and (with small gap between current and next word or in same context)
                        # we can merge current and next word in word the same word label

                        # add space if we are in same context ex : '(YELLOW' '5)' - > '(YELLOW 5)'
                        space = ""
                        if pa > 0:
                            if dist >= min_dist_thres and same_context:
                                space = " "

                        # build new word label that merge current and next word.
                        new_wl = {"text": wl["text"] + space + wl_1["text"]}
                        # union of 2 bb
                        xy1 = [
                            min(wl["bb"][0], wl_1["bb"][0]),
                            min(wl["bb"][1], wl_1["bb"][1]),
                        ]
                        xy2 = [
                            max(wl["bb"][2], wl_1["bb"][2]),
                            max(wl["bb"][3], wl_1["bb"][3]),
                        ]
                        new_wl["bb"] = tuple(map(int, (xy1[0], xy1[1], xy2[0], xy2[1])))
                        new_wl["bb_shapely"] = box(xy1[0], xy1[1], xy2[0], xy2[1])
                        new_wl["ul_shapely"] = multipoints(
                            [[xy1[0], xy2[1]], [xy2[0], xy2[1]]]
                        )
                        word_labels[index] = new_wl  # add new merged wl
                        del word_labels[index + 1]  # delete next merged wl
                        break  # reboot loop after word_labels list element deleted
    return word_labels


def word_labels_list_to_coco_dict(data):
    dataset_dict = []
    for d in data:
        filename_path = d["filename_path"]
        image = cv2.imread(filename_path)
        image_width, image_height = image.shape[1], image.shape[0]
        word_labels = d["word_labels"]
        entry = {
            "data": {
                "ocr": "http://localhost:8081/%s" % os.path.basename(filename_path)
            }
        }
        preds = []
        for word_label in word_labels:
            preds.append(
                {
                    "id": str(uuid4())[:10],
                    "from_name": "transcription",
                    "to_name": "image",
                    "type": "textarea",
                    "value": {
                        "text": [word_label["text"]],
                        "x": 100 * float(word_label["bb"][0]) / image_width,
                        "y": 100 * float(word_label["bb"][1]) / image_height,
                        "width": 100
                        * float(word_label["bb"][2] - word_label["bb"][0])
                        / image_width,
                        "height": 100
                        * float(word_label["bb"][3] - word_label["bb"][1])
                        / image_height,
                        "rotation": 0,
                    },
                }
            )
            entry["predictions"] = [{"result": preds}]
        dataset_dict.append(entry)
    return dataset_dict


def plot_bb(img, word_labels, color=(255, 255, 0), line_thickness=1):
    line_thickness = 2
    for label in word_labels:
        cv2.rectangle(
            img,
            label["bb"][0:2],
            label["bb"][2:4],
            color=color,
            thickness=line_thickness,
        )
    return img


def plot_bb_underline(img, word_labels, color=(255, 255, 0), line_thickness=1):
    line_thickness = 2
    for label in word_labels:
        cv2.rectangle(
            img,
            [label["bb"][i] for i in [0, 3]],
            label["bb"][2:4],
            color=color,
            thickness=line_thickness,
        )
    return img


def plot_text_labels(img, word_labels):
    image = Image.new("RGB", (img.shape[1], img.shape[0]), (255, 255, 255))
    image_editable = ImageDraw.Draw(image)
    for font_size in range(30, 10, -1):
        font = ImageFont.truetype("../data/ttf/other/NotoSans-Regular.ttf", font_size)
        too_large = False
        for label in word_labels:
            text_bb = image_editable.textbbox(
                label["bb"][0:2], text=label["text"], font=font, align="center"
            )
            text_width = text_bb[2] - text_bb[0]
            bb_width = label["bb"][2] - label["bb"][0]
            if text_width > bb_width:
                too_large = True
                break
        if not too_large:
            break
    for label in word_labels:
        image_editable.text(
            label["bb"][0:2],
            text=label["text"],
            fill=(0, 0, 0),
            font=font,
            align="center",
        )
    return asarray(image)
