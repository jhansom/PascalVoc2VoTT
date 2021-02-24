"""
VOC2VoTT.py

Converts Pascal VOC datasets into VoTT json datasets.
This script is for editing annotations after they have been exported, which VoTT does not support natively.
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from uuid import uuid1
from random import randint
from tqdm import tqdm


class VOC2VOTT:
    """
    Converts Pascal VOC datasets exported by VoTT into VoTT project files.
    """
    def __init__(self, root_dir, vott_file, output_dir):
        """
        Initializes the VOC2VOTT converter

        root_dir    :   Path to the root folder of the Pascal VOC dataset.
                        The root folder should contain the directories 'annotations', 'JPEGImages'
                        and the text file 'pascal_label_map.pbtxt'
        vott_file   :   Sample .vott project file to build VoTT project from
        output_dir  :   Directory to save VoTT project to
        """
        # Define paths used by script
        self.annotations = self._create_path(root_dir, 'annotations')
        self.image_dir = self._create_path(root_dir, 'JPEGImages')
        self.label_map = self._create_path(root_dir, 'pascal_label_map.pbtxt')
        self.tags_list = self.get_tags(self.label_map)
        self.vott_file = vott_file
        self.output_dir = output_dir

    def convert(self):
        """
        Converts Pascal VOC datasets exported by VoTT into VoTT project files.
        """
        # Read .vott file
        with open(self.vott_file) as vott_file:
            vott_data = json.load(vott_file)

        # Prepare .vott file
        vott_data['assets'] = {}
        vott_data['tags'] = []
        for tag in self.tags_list:
            vott_data["tags"].append(
                {
                    "name": tag,
                    "color": self._hexcode(randint(40, 200), randint(40, 200), randint(40, 200))
                }
            )
        # Read annotations
        for idx, entry in enumerate(tqdm(os.scandir(self.annotations))):
            if entry.name.endswith(".xml"):
                try:
                    asset_data = self._read_data_from_xml(entry.path)
                    if idx == 0:
                        vott_data['lastVisitedAssetId'] = asset_data['asset']['id']
                    vott_data['assets'][asset_data['asset']['id']] = asset_data['asset']
                    filename = f"{asset_data['asset']['id']}-asset.json"
                    with open(os.path.join(self.output_dir, filename), "w") as ov:
                        json.dump(asset_data, ov, indent=4, sort_keys=True)
                except:
                    print(f"Failed to parse file: {entry}", file=sys.st)

        # Prepare writing new .vott file
        vott_basename = os.path.basename(self.vott_file)
        vott_dst = os.path.join(self.output_dir, vott_basename)
        if os.path.exists(vott_dst):
            # If file already exists, back up old file before writing
            print(f"Naming conflict detected: Original {vott_dst} will be renamed as {vott_dst + '.old'}", file=sys.stderr)
            if os.path.exists(vott_dst + '.old'):
                os.remove(vott_dst + '.old') # Remove old backups, if necessary
            os.rename(vott_dst, vott_dst + '.old')

        # Write new .vott file
        with open(vott_dst, "w") as vott_file:
            json.dump(vott_data, vott_file, indent=4, sort_keys=True)


    def _read_data_from_xml(self, path_to_xml):
        """
        Returns a dictionary holding data structured as VoTT JSON annotations

        path_to_xml :   Path to Pascal VOC .xml annotation file
        """
        results = {}
        tree = ET.parse(path_to_xml)
        root = tree.getroot()
        xml_attr = {}
        xml_attr['path'] = self._create_path(self.image_dir, root.find('filename').text)
        xml_attr['size'] = root.find('size')
        results['asset'] = {}
        results['asset']['format'] = xml_attr['path'].split('.')[-1]
        results['asset']['id'] = str(uuid1()).replace("-", "")
        results['asset']['name'] = xml_attr['path'].split(os.sep)[-1]
        results['asset']['path'] = "file:" + xml_attr['path'].replace("\\", "/")
        results['asset']['size'] = {
            "width": int(xml_attr['size'].find('width').text),
            "height": int(xml_attr['size'].find('height').text)
        }
        results['asset']['state'] = 2
        results['asset']['type'] = 1
        results['regions'] = []
        for object_ in root.findall('object'):
            temp_region = {}
            temp_region['id'] = str(uuid1()).replace("-", "")
            temp_region['type'] = "RECTANGLE"
            temp_region['tags'] = [object_.find('name').text]
            obj_bnd_box = object_.find('bndbox')
            xmin = int(float(obj_bnd_box.find('xmin').text)) # Some exports give variables as floats
            ymin = int(float(obj_bnd_box.find('ymin').text))
            xmax = int(float(obj_bnd_box.find('xmax').text))
            ymax = int(float(obj_bnd_box.find('ymax').text))

            temp_region["boundingBox"] = {
                "height": ymax - ymin,
                "width": xmax - xmin,
                "left": xmin,
                "top": ymin
            }
            temp_region['points'] = [
                {
                    "x": xmin,
                    "y": ymin
                },
                {
                    "x": xmax,
                    "y": ymin
                },
                {
                    "x": xmax,
                    "y": ymax
                },
                {
                    "x": xmin,
                    "y": ymax
                }
            ]
            results['regions'].append(temp_region)
        results['version'] = "2.1.0"
        return results


    def get_tags(self, label_map_path):
        """
        Returns a list of tags from a .pbtxt label map

        label_map_path  : Path to label map .pbtxt file from Pascal VOC dataset
        """
        with open(label_map_path) as infile:
            # Grab all lines that have tag names on it
            lines = [line.strip() for line in infile.readlines() if 'name' in line] 
        # Strip quotes off of the string and grab the name
        return [line.replace("'", "").split()[-1] for line in lines] 


    def _create_path(self, prefix, suffix):
        """
        Returns a normalized absolute path

        prefix  :   Left hand side of the path
        suffix  :   Right hand side of the path
        """
        path = os.path.join(prefix, suffix)
        path = os.path.normpath(path)
        path = os.path.abspath(path)
        path = os.path.normpath(path)
        return path


    def _hexcode(self, r=None, g=None, b=None):
        """
        Returns a string containing a hexcode. If a value for a channel is not 
        specified, a random value is chosen. Values outside of the range [0, 255]
        are automatically clamped

        r   :   Value for the red channel, if r=None a random value is picked
        g   :   Value for the green channel, if g=None a random value is picked
        b   :   Value for the blue channel, if b=None a random value is picked
        """
        def _chkarg(a):
            # Handle unspecified and invalid values
            if a is None:
                a = randint(0, 255)
            return int(max(0, min(a, 255)))

        r, g, b = map(_chkarg, [r,g,b])
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)



if __name__ == '__main__':
    DESCRIPTION = """\
        Converts Pascal VOC datasets into VoTT json datasets.
        This script is for editing annotations after they have been exported, which VoTT does not support natively.
        """
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog='\n\n ', formatter_class=argparse.RawDescriptionHelpFormatter)
    required_args = parser.add_argument_group('required arguments')
    required_args.add_argument('--pascal_voc_dir', type=str, help='Path to the directory exported by VoTT', required=True)
    required_args.add_argument('--vott_file', type=str, help='Path to .vott project file to convert to', required=True)
    required_args.add_argument("--out_dir", type=str, help='Path to output VoTT project and annotations at', required=True)
    args = parser.parse_args()

    print()
    print("Creating VoTT dataset from Pascal VOC dataset...")
    print()
    print("Original Pascal VOC dataset location")
    print(f'\t{args.pascal_voc_dir}')
    print()

    voc2vott = VOC2VOTT(
        root_dir=args.pascal_voc_dir,
        vott_file=args.vott_file,
        output_dir=args.out_dir
    )
    voc2vott.convert()

    print()
    print("Conversion complete!")
    print(f"VoTT project file and annotations saved to {args.out_dir}\n\n")

