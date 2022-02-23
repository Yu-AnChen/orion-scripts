import palom
import numpy as np
import skimage.segmentation
import dask.array as da

def construct_channel(
    img_path,
    channel,
    process_func=None
):
    reader = palom.reader.OmePyramidReader(img_path)
    if process_func is None:
        return reader.pyramid[0][channel]
    return process_func(reader.pyramid[0][channel])

def mask_to_bound(
    img_da,
    overlap_depth=100,
    out_dtype=np.uint16,
    positive_value=45535
):
    return img_da.map_overlap(
        skimage.segmentation.find_boundaries,
        depth=overlap_depth
    ).astype(out_dtype) * positive_value

def run(
    settings,
    output_path,
    pixel_size,
    channel_names
):
    mosaics = []
    for setting in settings:
        mosaics.append(
            construct_channel(setting[0], setting[1], setting[2])
        )
    palom.pyramid.write_pyramid(
        [da.array(mosaics)],
        output_path,
        pixel_size,
        channel_names
    )
    return


C01 = [
    (
        r"Z:\RareCyte-S3\P37_CRCstudy_Round1\P37_S27_Full_A24_C59kX_E15@20220106_002943_210932.ome.tiff",
        0,
        None
    ),
    (
        r'Z:\RareCyte-S3\YC-analysis\P37_CRCstudy_Round1\P37_S27-CRC40\segmentation\P37_S27_Full_A24_C59kX_E15@20220106_002943_210932\nucleiRingMask.tif',
        0,
        mask_to_bound
    ),
    (
        r"Z:\RareCyte-S3\P37_CRCstudy_Round1_HE\registered\P37_S27_HE3@20220131_213326_312413.pysed.ome-registered.ome.tif",
        2,
        None
    )
]
channel_names = [(
    'Hoechst',
    'Nucleus mask',
    'HE-B'
)]

run(
    C01,
    r"Z:\RareCyte-S3\P37_CRCstudy_Round1_HE\registered\QC-hoechst_mask_he\P37_S27-hoechst_mask_he.ome.tif",
    0.325,
    channel_names
)


    # img_if = palom.reader.OmePyramidReader()
    # img_mask = palom.reader.OmePyramidReader(r"Z:\RareCyte-S3\YC-analysis\P37_CRCstudy_Round1\P37_S29-CRC01\segmentation\P37_S29_A24_C59kX_E15@20220106_014304_946511\nucleiRingMask.tif")
    # img_mask_bounds = img_mask.pyramid[0].map_overlap(skimage.segmentation.find_boundaries, depth=100)
    # img_he = palom.reader.OmePyramidReader(r"Z:\RareCyte-S3\P37_CRCstudy_Round1_HE\registered\P37_S29_HE3@20220201_210011_464018.pysed.ome-registered.ome.tif")
    # mosaics = [img_if.pyramid[0][0], img_mask_bounds.astype(np.uint16)*45535, da.invert(img_he.pyramid[0][1])]


# import palom
# img_mask = palom.reader.OmePyramidReader(r"Z:\RareCyte-S3\YC-analysis\P37_CRCstudy_Round1\P37_S29-CRC01\segmentation\P37_S29_A24_C59kX_E15@20220106_014304_946511\nucleiRingMask.tif")
# img_if = palom.reader.OmePyramidReader(r"Z:\RareCyte-S3\P37_CRCstudy_Round1\P37_S29_A24_C59kX_E15@20220106_014304_946511.ome.tiff")
# img_mask.pyramid
# import skimage.segmentation
# skimage.segmentation.find_boundaries?
# img_if.pyramid
# img_mask.pyramid
# img_mask.pyramid[0].map_overlap?
# img_mask.pyramid[0].map_overlap
# import dask.array as da
# da.map_overlap
# mmm = img_mask.pyramid[0][0, 30000:35000, 35000:35000]
# pylab
# mmm = img_mask.pyramid[0][0, 30000:35000, 35000:35000].compute()
# figure(); imshow(mmm)
# mmm = img_mask.pyramid[0][0, 30000:35000, 30000:35000].compute()
# figure(); imshow(mmm)
# mmm = skimage.segmentation.find_boundaries(img_mask.pyramid[0][0, 30000:35000, 30000:35000].compute())
# mmm2 = img_mask.pyramid[0][0, 30000:35000, 30000:35000].map_overlap(skimage.segmentation.find_boundaries, depth=100)
# mmm2 = img_mask.pyramid[0][0, 30000:35000, 30000:35000].map_overlap(skimage.segmentation.find_boundaries, depth=100).compute()
# np.sum(mmm != mmm2)
# figure(); imshow(mmm2)
# img_mask_bounds = img_mask.pyramid[0].map_overlap(skimage.segmentation.find_boundaries, depth=100)

# #img_mask_bounds = img_mask.pyramid[0].map_overlap(skimage.segmentation.find_boundaries, depth=100)
# img_mask.pyarmid[0]
# img_mask
# img_mask.pyramid[0]
# img_mask_bounds = img_mask.pyramid[0][0].map_overlap(skimage.segmentation.find_boundaries, depth=100)
# img_mask_bounds
# palom.pyramid.write_pyramid?
# da.invert
# img_mask_bounds.astype(np.uint16)*45535
# img_he = palom.reader.OmePyramidReader(r"Z:\RareCyte-S3\P37_CRCstudy_Round1_HE\registered\P37_S29_HE3@20220201_210011_464018.pysed.ome-registered.ome.tif")
# img_he.yramid
# img_he.pyramid
# da.invert(img_he.pyramid[0][1])
# mosaics = [img_if.pyramid[0][0], img_mask_bounds.astype(np.uint16)*45535, da.invert(img_he.pyramid[0][1])]
# palom.pyramid.write_pyramid?
# #palom.pyramid.write_pyramid(mosaics, r"Z:\RareCyte-S3\P37_CRCstudy_Round1_HE\registered\QC-hoechst_mask_he\P37_S29-hoechst_mask_he.ome.tif", pixel_size=0.325, channel_names=['Hoechst', 'Nucleus mask', 'HE-G'])