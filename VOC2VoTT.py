"""
VOC2VoTT.py

Creates a VoTT project and annotations from a Pascal VOC dataset.
"""
import os
import random
import string
import sys
import json
import argparse
import xml.etree.ElementTree as eT
from uuid import uuid1
from tqdm import tqdm


class VOC2VoTT:
    """
    Creates a VoTT project and annotations from a Pascal VOC dataset.
    """

    def __init__(self, in_path, out_path, name):
        """
        Initializes the VOC2VoTT converter

        in_path : Path to the Pascal VOC dataset.
        The folder should contain the subfolders 'annotations' and 'images'
        and the text file 'pascal_label_map.pbtxt'.
        out_path : Path to save VoTT project and annotations to.
        name : The name to give the created VoTT project.
        """
        # Define paths used by script
        self.in_path = in_path
        self.annotations_path = self._create_path(in_path, 'annotations')
        self.images_path = self._create_path(in_path, 'images')

        if not os.path.exists(self.in_path):
            print(f"Your input folder doesn't exist.", file=sys.stderr)
            sys.exit(1)

        if not os.path.exists(self.images_path) or not os.path.exists(self.annotations_path):
            print(f"Your input dataset should be separated into 'annotations' and 'images' subfolders.",
                  file=sys.stderr)
            sys.exit(1)

        self.label_map = self._create_path(in_path, 'pascal_label_map.pbtxt')
        self.tags_list = self._get_tags(self.label_map)

        if self.tags_list is None:
            print(f"You need to provide a label map named 'pascal_label_map.pbtxt'.\n"
                  f"It should be placed in your input folder.", file=sys.stderr)
            sys.exit(1)

        self.out_path = out_path
        self.name = name

    def convert(self):
        """
        Does the conversion.
        """

        # Generate .vott file.
        vott_dst = os.path.join(self.out_path, self.name + '.vott')

        vott_data = {}
        vott_data['name'] = self.name

        vott_data['sourceConnection'] = {}
        vott_data['sourceConnection']['name'] = self.name + 'Source'
        vott_data['sourceConnection']['providerType'] = 'localFileSystemProxy'
        vott_data['sourceConnection']['providerOptions'] = {}
        vott_data['sourceConnection']['providerOptions']['folderPath'] = self.images_path
        vott_data['sourceConnection']['providerOptions']['relativePath'] = True
        vott_data['sourceConnection']['id'] = self._generate_id()

        vott_data['targetConnection'] = {}
        vott_data['targetConnection']['name'] = self.name + 'Target'
        vott_data['targetConnection']['providerType'] = 'localFileSystemProxy'
        vott_data['targetConnection']['providerOptions'] = {}
        vott_data['targetConnection']['providerOptions']['folderPath'] = self.out_path
        vott_data['targetConnection']['providerOptions']['relativePath'] = True
        vott_data['targetConnection']['id'] = self._generate_id()

        vott_data['videoSettings'] = {}
        vott_data['videoSettings']['frameExtractionRate'] = 15
        vott_data['useSecurityToken'] = False
        vott_data['securityToken'] = ""
        vott_data['id'] = self._generate_id()

        vott_data['activeLearningSettings'] = {}
        vott_data['activeLearningSettings']['autoDetect'] = False
        vott_data['activeLearningSettings']['predictTag'] = True
        vott_data['activeLearningSettings']['modelPathType'] = 'coco'

        vott_data['exportFormat'] = {}
        vott_data['exportFormat']['providerType'] = 'vottJson'
        vott_data['exportFormat']['providerOptions'] = {}
        vott_data['exportFormat']['providerOptions']['assetState'] = 'visited'
        vott_data['exportFormat']['providerOptions']['includeImages'] = True

        vott_data['version'] = '2.2.0'

        # Add tags.
        vott_data['assets'] = {}
        vott_data['tags'] = []
        for tag in self.tags_list:
            vott_data["tags"].append(
                {
                    "name": tag,
                    "color": self._hexcode(random.randint(40, 200), random.randint(40, 200),
                                           random.randint(40, 200))
                }
            )

        # Convert and add annotations.
        listing = os.listdir(self.annotations_path)
        listing.sort()
        for idx, entry in enumerate(tqdm(listing)):
            if entry.endswith(".xml"):
                asset_data = self._read_data_from_xml(self._create_path(self.annotations_path, entry))
                if asset_data is None:
                    print(f'Failed to parse file: {self._create_path(self.annotations_path, entry)}', file=sys.stderr)
                    sys.exit(1)

                if idx == 0:
                    vott_data['lastVisitedAssetId'] = asset_data['asset']['id']
                vott_data['assets'][asset_data['asset']['id']] = asset_data['asset']
                filename = f"{asset_data['asset']['id']}-asset.json"
                try:
                    with open(os.path.join(self.out_path, filename), "w") as ov:
                        try:
                            json.dump(asset_data, ov, indent=4, sort_keys=True)
                        except (TypeError, ValueError, RecursionError):
                            print(f'Error writing JSON to {filename}.', filename, file=sys.stderr)
                            sys.exit(1)
                except OSError:
                    print(f'Error opening file {filename}.', filename, file=sys.stderr)
                    sys.exit(1)

        if os.path.exists(vott_dst):
            # If project file already exists, backup current version before writing.
            print(f"{vott_dst} exists! Backing-up to {vott_dst + '.old'}")
            try:
                if os.path.exists(vott_dst + '.old'):
                    os.remove(vott_dst + '.old')  # Remove old backups, if necessary
                os.rename(vott_dst, vott_dst + '.old')
            except OSError:
                print(f'Error occurred backing-up project file.', file=sys.stderr)
                sys.exit(1)

        # Write new .vott file
        try:
            with open(vott_dst, "w") as vott_file:
                json.dump(vott_data, vott_file, indent=4, sort_keys=False)
        except OSError:
            print(f'Error occurred writing project file.', file=sys.stderr)
            sys.exit(1)

    def _read_data_from_xml(self, path_to_xml):
        """
        Returns a dictionary holding data structured as VoTT JSON annotations

        path_to_xml : Path to Pascal VOC .xml annotation file
        """
        results = {}

        try:
            tree = eT.parse(path_to_xml)
        except eT.ParseError as e:
            return None

        root = tree.getroot()
        xml_attr = {'path': self._create_path(self.images_path, root.find('filename').text), 'size': root.find('size')}
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
            temp_region = {'id': str(uuid1()).replace("-", ""), 'type': "RECTANGLE",
                           'tags': [object_.find('name').text]}
            obj_bnd_box = object_.find('bndbox')
            xmin = int(float(obj_bnd_box.find('xmin').text))  # Some exports give variables as floats
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
        results['version'] = "2.2.0"
        return results

    @staticmethod
    def _get_tags(label_map_path):
        """
        Returns a list of tags from a .pbtxt label map

        label_map_path : Path to label map .pbtxt file from Pascal VOC dataset
        """
        try:
            with open(label_map_path) as infile:
                # Grab all lines that have tag names on it
                lines = [line.strip() for line in infile.readlines() if 'name' in line]
        except OSError:
            return None
        # Strip quotes off of the string and grab the name
        return [line.replace("'", "").split()[-1] for line in lines]

    @staticmethod
    def _create_path(prefix, suffix):
        """
        Returns a normalized absolute path

        prefix : Left hand side of the path
        suffix : Right hand side of the path
        """
        path = os.path.join(prefix, suffix)
        path = os.path.normpath(path)
        path = os.path.abspath(path)
        path = os.path.normpath(path)
        return path

    @staticmethod
    def _hexcode(r=None, g=None, b=None):
        """
        Returns a string containing a hexcode. If a value for a channel is not
        specified, a random value is chosen. Values outside of the range [0, 255]
        are automatically clamped

        r : Value for the red channel, if r=None a random value is picked
        g : Value for the green channel, if g=None a random value is picked
        b : Value for the blue channel, if b=None a random value is picked
        """

        def _chkarg(a):
            # Handle unspecified and invalid values
            if a is None:
                a = random.randint(0, 255)
            return int(max(0, min(a, 255)))

        r, g, b = map(_chkarg, [r, g, b])
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    @staticmethod
    def _generate_id():
        """
        Generate an ID compatible with the VoTT project file format.
        """

        hyphen_pos = random.randint(1, 8)
        conn_id = (''.join(random.choices(string.ascii_letters + string.digits, k=hyphen_pos)) + '-' +
                   ''.join(random.choices(string.ascii_letters + string.digits, k=8 - hyphen_pos)))
        return conn_id


def main():
    docstring = """
    Creates a VoTT project and annotations from a Pascal VOC dataset.
    """
    parser = argparse.ArgumentParser(description=docstring, epilog='\n\n ',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--in_path', type=str, help='Path of the Pascal VOC dataset', required=False)
    parser.add_argument('--out_path', type=str, help='Path to save the VoTT project and annotations to',
                        required=False)
    parser.add_argument('--name', type=str, help='Name to give the created VoTT project', required=True)
    args = parser.parse_args()

    if args.in_path is None:
        args.in_path = os.getcwd()
    if args.out_path is None:
        args.out_path = os.getcwd()

    print()
    print(f"Converting Pascal VOC dataset located at {args.in_path} ...")
    print()

    voc2vott = VOC2VoTT(
        in_path=args.in_path,
        out_path=args.out_path,
        name=args.name
    )
    voc2vott.convert()

    print()
    print("Conversion complete!")
    print(f"VoTT project file and annotations saved to {args.out_path}\n\n")


if __name__ == '__main__':
    main()
