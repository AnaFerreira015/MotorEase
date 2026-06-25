import xml.etree.ElementTree as ET
from PIL import Image
import cv2
import os
import importlib

foobar = importlib.import_module("detectors.Visual.UIED-master.run_single")
import json
from detectors.bounds_utils import normalize_bounds


def __init__(self):
    pass


def getBounds(inText):
    split = inText.split('][')

    split[0] = split[0].strip('[')
    split[1] = split[1].strip(']')

    split[0] = split[0].split(",")
    split[1] = split[1].split(",")

    split[0] = [int(split[0][0]), int(split[0][1])]
    split[1] = [int(split[1][0]), int(split[1][1])]
    return split


def checkTouchTarget(screenshot_path, xml_path, min_size=(48, 48)):
    if ".DS_S" in xml_path:
        return [0, 0, xml_path, []]

    tree = ET.parse(xml_path)
    root = tree.getroot()
    violations = 0
    nonViolations = 0
    violationBounds = []

    for elem in root.iter():
        elements = elem.items()
        if len(elements) > 1:
            if elements[8][0] == 'clickable' and elements[8][1] == 'true' and elements[16][1] != '[0,0][0,0]':
                bounds = getBounds(elements[16][1])
                first = bounds[1][0] - bounds[0][0]
                second = bounds[1][1] - bounds[0][1]

                if first < 48 or second < 48:
                    violations += 1
                    violationBounds.append({
                        "guideline": "Touch Target Size",
                        "bounds": normalize_bounds(bounds),
                        "source": "xml"
                    })
                else:
                    im = Image.open(screenshot_path)
                    cropX = bounds[0][0] - 15  # origem do recorte
                    cropY = bounds[0][1] - 15
                    im1 = im.crop((cropX, cropY, bounds[1][0] + 15, bounds[1][1] + 15))
                    savePath = "./Code/detectors/Visual/UIED-master/data/input/" + str(screenshot_path.split('/')[-1])
                    im1.save(savePath)
                    foobar.runSingle(savePath)
                    os.remove(savePath)

                    for r, dirs, files_in_dir in os.walk("./Code/detectors/Visual/UIED-master/data/output/ip/"):
                        for file_name in files_in_dir:
                            if ".json" in file_name:
                                with open("./Code/detectors/Visual/UIED-master/data/output/ip/" + file_name, "r") as f:
                                    data = json.load(f)
                                for i in range(len(data["compos"])):
                                    c = data["compos"][i]
                                    if c['height'] < 48 or c['width'] < 48:
                                        violations += 1
                                        violationBounds.append({
                                            "guideline": "Visual Touch Target Size",
                                            "bounds": [
                                                cropX + c['column_min'],
                                                cropY + c['row_min'],
                                                cropX + c['column_max'],
                                                cropY + c['row_max'],
                                            ],
                                            "source": "visual"
                                        })
                                    else:
                                        nonViolations += 1
                                os.remove("./Code/detectors/Visual/UIED-master/data/output/ip/" + file_name)
                    im.close()

    return [violations, violations + nonViolations, xml_path, violationBounds]
