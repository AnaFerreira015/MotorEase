print(">> Starting MotorEase\n")
import os
# from application.app.folder.file import func_name
from detectors.Visual.TouchTarget import checkTouchTarget
from detectors.Visual.IconDistance import getDistance
# from detectors.Visual.LabeledElements import checkLabeled
from detectors.Motor.Closure import *
from detectors.Motor.Closure import detectClosure
from detectors.Motor.patternMatching.pattern_matching import *
from detectors.Motor.persistentElements import *
from detectors.Motor.persistentElements import PersistentDriver
import pickle
from numpy import asarray
import json

import importlib

pre = importlib.import_module("detectors.Visual.UIED-master.detect_compo.lib_ip.ip_preprocessing")
draw = importlib.import_module("detectors.Visual.UIED-master.detect_compo.lib_ip.ip_draw")
det = importlib.import_module("detectors.Visual.UIED-master.detect_compo.lib_ip.ip_detection")
file = importlib.import_module("detectors.Visual.UIED-master.detect_compo.lib_ip.file_utils")
Compo = importlib.import_module("detectors.Visual.UIED-master.detect_compo.lib_ip.Component")
ip = importlib.import_module("detectors.Visual.UIED-master.detect_compo.ip_region_proposal")
Congfig = importlib.import_module("detectors.Visual.UIED-master.config.CONFIG_UIED")


def RunDetectors(data_folder, out_name="AccessibilityReport.json"):
    print(">> Extracting Path\n")
    txt = open("AccessibilityReportTEXT.txt", "a")
    txt = open("predictions2.txt", "a")
    report = {}
    print(">> Getting Files and Screenshots\n")

    # Coleta pares (png + xml) de forma robusta, sem depender da ordem do os.walk
    bases = set()
    for root, dirs, files_in_dir in os.walk(data_folder):
        for file_name in files_in_dir:
            if "DS_S" in file_name:
                continue
            if file_name.lower().endswith((".png", ".xml")):
                base = os.path.join(root, os.path.splitext(file_name)[0]).replace('\\', '/')
                bases.add(base)
    files = sorted(bases)

    print(">> Initializing Detectors\n")
    print(">> Initializing Embedding Model (may take some time)\n")

    model = {}
    with open("C:/Projetos/MotorEase/ana_MotorEase/MotorEase/Code/glove.6B.300d.txt", 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            word = parts[0]
            vector = [float(x) for x in parts[1:]]  # Convert string components to floats
            model[word] = vector

    glove_model_array = model

    for base in files:
        image = base + ".png"
        xml = base + ".xml"
        if not (os.path.exists(image) and os.path.exists(xml)):
            print(">> Pulando tela sem par completo: " + base)
            continue
        screen = os.path.basename(base) + ".png"
        report.setdefault(screen, {"errors": []})
        txt.write("============================================\n")
        txt.write('FILENAME: ' + screen + "\n")

        print("_______Analyzing Next File______")

        print("===== Running Touch Target =====")
        touchTarget = checkTouchTarget(image, xml)  # Format-> [violations, elements, xml_path, violationBounds]
        touchText = "Touch Target Detector>> " + "Interactive Elements: " + str(
            touchTarget[1]) + " | Violating Elements: " + str(touchTarget[0]) + "\n"
        print(touchText)
        txt.write(touchText + '\n')
        report[screen]["errors"].extend(touchTarget[3])  # bounds do touch target

        print("===== Running Expanding Elements =====")
        expanding = detectClosure(image, xml, glove_model_array)
        expandingText = image + ":\n" + "Expanding Sections Detector>> " + "Expanding elements: " + str(
            expanding) + "\n"
        print(expandingText)
        txt.write(expandingText + '\n')
        print("\n")

        print("===== Running Icon Distances =====")
        distances = getDistance(image, xml)  # Format-> [0 ou 1, violationBounds]
        print(distances)
        txt.write(screen + ', ' + str(distances) + "\n")
        report[screen]["errors"].extend(distances[1])  # pares do icon distance
        print("\n")

    txt.write("============================================\n")
    txt.write("\nAll Screens \n")
    print("_______Analyzing All Screens_______")
    print("===== Running Persistent Elements =====")
    persistent = PersistentDriver(data_folder)  # Format-> [allViolations, noViolations, violationDetails]
    persistentText = data_folder + ': \n' "Persisting Elements Detector>> " + "Violating Screens: " + str(persistent[1])
    print(persistentText)

    for v in persistent[2]:  # detalhes com bounds (cross-screen)
        report.setdefault(v["screen"], {"errors": []})
        report[v["screen"]]["errors"].append({
            "guideline": v["guideline"],
            "element_id": v["element_id"],
            "bounds": v["bounds"]
        })

    print("\n>> Generating Accessibility Report")
    txt.write(persistentText + '\n')

    with open(out_name, "w", encoding="utf-8") as jf:
        json.dump(report, jf, indent=2, ensure_ascii=False)

    print("\nAccessibility Report Generated: AccessibilityReport.txt")
    print("JSON gerado: AccessibilityReport.json")

    txt.close()


# set the path to the directory of the Miracle Project
import sys
MotorEase_PATH = "C:/Projetos/MotorEase/ana_MotorEase/MotorEase/"
os.chdir(MotorEase_PATH)

if len(sys.argv) > 1:
    # roda na pasta passada por argumento (ex: uma subpasta de motorease_input)
    AppPath = sys.argv[1]
    folder_id = os.path.basename(os.path.normpath(AppPath))
    out_name = "AccessibilityReport_" + folder_id + ".json"
else:
    # comportamento padrao: pasta Data do projeto
    AppPath = MotorEase_PATH + 'Data'
    out_name = "AccessibilityReport.json"

print(">> Pasta de dados:", AppPath)
print(">> Saida JSON:", out_name)
RunDetectors(AppPath, out_name)