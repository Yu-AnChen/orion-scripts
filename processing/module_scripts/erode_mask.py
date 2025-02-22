import palom
import skimage.morphology


def process_slide(
    nucleus_mask_path, cell_mask_path, erode_size, output_path, _overlap_size=128
):
    assert erode_size > 0
    assert erode_size == int(erode_size)
    r1 = palom.reader.OmePyramidReader(nucleus_mask_path)
    r2 = palom.reader.OmePyramidReader(cell_mask_path)

    nucleus = r1.pyramid[0][0]
    cell = r2.pyramid[0][0]
    eroded = nucleus.astype(bool).map_overlap(
        skimage.morphology.binary_erosion,
        footprint=skimage.morphology.disk(erode_size),
        depth={0: _overlap_size, 1: _overlap_size},
    )

    mask = cell - (nucleus * eroded)

    palom.pyramid.write_pyramid(
        [mask],
        output_path,
        pixel_size=r1.pixel_size,
        downscale_factor=2,
        compression="zlib",
        is_mask=True,
        save_RAM=True,
    )


import argparse
import pathlib
import sys


def get_parser():
    """Creates and returns an argument parser for the erode_mask.py script."""
    parser = argparse.ArgumentParser(
        description="Erodes a nucleus mask and processes it against a cell mask."
    )

    parser.add_argument(
        "nucleus_mask_path",
        type=pathlib.Path,
        help="Path to the input nucleus mask (OME-TIFF file).",
    )

    parser.add_argument(
        "cell_mask_path",
        type=pathlib.Path,
        help="Path to the input cell mask (OME-TIFF file).",
    )

    parser.add_argument(
        "erode_size",
        type=int,
        help="Size of the erosion element in pixels.",
    )

    parser.add_argument(
        "output_path",
        type=pathlib.Path,
        help="Path to save the processed mask (OME-TIFF file).",
    )

    return parser


def main(argv=sys.argv):
    parser = get_parser()
    args = parser.parse_args(argv[1:])

    process_slide(
        nucleus_mask_path=args.nucleus_mask_path,
        cell_mask_path=args.cell_mask_path,
        erode_size=args.erode_size,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    sys.exit(main())
