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
