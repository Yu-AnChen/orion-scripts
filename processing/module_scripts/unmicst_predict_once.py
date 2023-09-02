# conda create -n test-unmicst -c conda-forge python=3.10
# conda activate test-unmicst
# https://www.tensorflow.org/install/pip#windows-native
# conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0
# python -m pip install "tensorflow<2.11"
# python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
# python -m pip install scikit-image ipython matplotlib czifile nd2reader joblib tifffile zarr dask_image


import datetime
import os
import pathlib
import sys
import time
import warnings

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import dask.array as da
import dask.diagnostics
import dask_image.ndinterp
import numpy as np
import skimage.exposure
import skimage.util
import tifffile
import zarr

CURR = pathlib.Path(__file__).resolve().parent
unmicst_path = CURR.parent.parent / 'modules' / 'UnMicst'
sys.path.append(str(unmicst_path))

import UnMicst2 as UnMicst2

from . import rowit


def www4(img, border_size=24, out_dtype=None):
    # return np.ones((*img.shape[:2], 3), np.float32)
    assert img.ndim == 3
    assert img.shape[0] in [1, 2, 3]
    assert border_size >= 0

    img = img[:2]
    border_size = int(border_size)
    C, Y, X = img.shape
    
    wv_cfg = rowit.WindowView((Y, X), 128, 2*border_size)
    out_size = 128 - 2*border_size
    wv_imgs = [
        wv_cfg.window_view_list(channel)
        for channel in img
    ]
    first_wv_img = wv_imgs[0]
    n_patches = len(first_wv_img)
    output = np.zeros((n_patches, out_size, out_size, 3), dtype=np.float32)

    start = border_size if border_size > 0 else None
    end = -border_size if border_size > 0 else None
    for i in range(0, n_patches, 24):
        batch = np.zeros((24, 128, 128, C))
        n_sub_patches = len(first_wv_img[i:i+24])
        for cc, wv_img in zip(range(C), wv_imgs):
            batch[:n_sub_patches, ..., cc] = wv_img[i:i+24]
        batch -= 0.18
        batch /= 0.17
        output[i:i+24] = UnMicst2.UNet2D.Session.run(
            UnMicst2.UNet2D.nn,
            feed_dict={UnMicst2.UNet2D.tfData: batch, UnMicst2.UNet2D.tfTraining: 0}
        )[:n_sub_patches, start:end, start:end]
    output = skimage.util.montage(
        output,
        grid_shape=wv_cfg.window_view_shape[:2],
        channel_axis=3
    )[:Y, :X]
    if out_dtype is not None:
        output = skimage.exposure.rescale_intensity(
            output, in_range=(0, 1), out_range=out_dtype
        ).astype(out_dtype)
    return np.moveaxis(output, 2, 0)


def da_to_zarr(da_img, zarr_store=None, num_workers=None, out_shape=None, chunks=None):
    if zarr_store is None:
        if out_shape is None:
            out_shape = da_img.shape
        if chunks is None:
            chunks = da_img.chunksize
        zarr_store = zarr.create(
            out_shape,
            chunks=chunks,
            dtype=da_img.dtype,
            overwrite=True
        )
    with dask.diagnostics.ProgressBar():
        da_img.to_zarr(zarr_store, compute=False).compute(
            num_workers=num_workers
        )
    return zarr_store


model_path = pathlib.Path(unmicst_path / 'models' / 'nucleiDAPILAMIN')
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    UnMicst2.UNet2D.singleImageInferenceSetup(model_path, 0, -1, -1)


# 
# Process input
# 
def process_slide(
    img_path,
    nucleus_channel,
    size_scaling_factor=1,
    intensity_in_range_p0=0,
    intensity_in_range_p1=100,
    intensity_min=None,
    intensity_max=None,
    # intensity_min=400,
    # intensity_max=8000,
    output_path=None,
    intensity_gamma=0.8,
    other_channels=None,
    save_RAM=False
):
    start = int(time.perf_counter())

    img_path = pathlib.Path(img_path)
    if output_path is None:
        output_path = img_path.parent / f"{img_path.stem}-pmap.ome.tif"
    else:
        output_path = pathlib.Path(output_path)
        out_name = output_path.name
        assert out_name.endswith('.ome.tif') or out_name.endswith('.ome.tiff')

    if save_RAM:
        img = zarr.open(tifffile.imread(
            img_path, key=nucleus_channel, aszarr=True
        ), mode='r')
        da_img = da.from_zarr(img, chunks=2048)
    else:
        img = tifffile.imread(img_path, key=nucleus_channel)
        da_img = da.from_array(img, chunks=2048)
    print('Image shape:', da_img.shape)
    H, W = da_img.shape

    mx = np.eye(3) * size_scaling_factor
    mx[-1, -1] = 1
    out_shape = np.ceil(size_scaling_factor*np.array([H, W])).astype(int)

    # resize to match model training input
    transformed_img = da_img
    if size_scaling_factor != 1:
        transformed_img = dask_image.ndinterp.affine_transform(
            da_img,
            matrix=np.linalg.inv(mx),
            output_chunks=(1024, 1024),
            output_shape=out_shape
        )
    
    # rescale intensity
    quantiles = []
    intensity_ps = []
    if intensity_min is None:
        quantiles.append(intensity_in_range_p0)
    if intensity_max is None:
        quantiles.append(intensity_in_range_p1)
    if len(quantiles) > 0:
        intensity_ps = np.percentile(img, quantiles)
    in_range = np.array(
        [*intensity_ps, intensity_min, intensity_max],
        dtype=float
    )
    in_range = np.sort(in_range)[:2]
    print('\nin_range:', tuple(in_range), '\n')
    transformed_img = (
        transformed_img
        .map_blocks(
            skimage.exposure.rescale_intensity,
            in_range=tuple(in_range),
            out_range=np.float32,
            dtype=np.float32
        )
        .map_blocks(
            skimage.exposure.adjust_gamma,
            gamma=intensity_gamma,
            dtype=np.float32
        )
    )
    transformed_img *= 0.95

    # compute once
    zarr_transformed_img = da_to_zarr(transformed_img)

    # model-ready image, rechunk into (3, TS, TS) seems to be needed
    stack_img = da.array([da.from_zarr(zarr_transformed_img)]*3).rechunk(1024)

    prob_maps = stack_img.map_overlap(
        www4,
        out_dtype=np.uint8,
        depth={0:0, 1:32, 2:32},
        boundary='none',
        dtype=np.uint8
    )

    zarr_prob_maps = da_to_zarr(
        prob_maps,
        num_workers=1
    )

    # final resizing
    zarr_matched_prob_maps = zarr_prob_maps
    if size_scaling_factor != 1:
        matched_prob_maps = dask_image.ndinterp.affine_transform(
            da.from_zarr(zarr_prob_maps, chunks=zarr_prob_maps.chunks),
            matrix=np.roll(mx, 1, axis=(0, 1)),
            output_chunks=(1, 2048, 2048),
            output_shape=(3, H, W)
        )

        zarr_matched_prob_maps = da_to_zarr(matched_prob_maps)

    end = int(time.perf_counter())
    print('\nelapsed (unet):', datetime.timedelta(seconds=end - start))

    import palom

    palom.pyramid.write_pyramid(
        [da.from_zarr(zarr_matched_prob_maps)[[2, 1, 0], ...]],
        output_path,
        pixel_size=0.325,
        downscale_factor=2,
        tile_size=1024,
        compression='zlib',
        save_RAM=True,
        kwargs_tifffile=dict(software='unmicst v2.7.1')
    )

    end = int(time.perf_counter())
    print('\nelapsed (total):', datetime.timedelta(seconds=end - start))
