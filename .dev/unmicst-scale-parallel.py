# Using the nucleiDAPILAMIN model instead of the nucleiDAPI model

import sys
sys.path.append('/home/ychen/mcmicro/UnMicst')

import UnMicst2 as UnMicst2
import pathlib
import skimage.io
import skimage.exposure
import rowit
import skimage.transform
from joblib import Parallel, delayed
import numpy as np
import warnings
import time
import datetime
import tifffile


def wrap_rescale(img, scale=1, kwargs={}):
    if scale == 1: return img
    return skimage.transform.rescale(img, scale, **kwargs)

def wrap_round_dtype(img, dtype=None):
    if dtype is None: return img
    assert np.issubdtype(dtype, np.integer), 'dtype must be subtype of np.integer'
    d_info = np.iinfo(dtype)
    return np.clip(np.round(img), d_info.min, d_info.max).astype(dtype)


def whole_image_bg(img, method, radius):
    ori_img = img

    func = getattr(skimage.filters.rank, method)

    def wrap_warn(rank_func, img, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return rank_func(img, **kwargs)

    wv_bg = Parallel(n_jobs=1, max_nbytes=None, verbose=1)(
        delayed(wrap_warn)(
            func, i, selem=skimage.morphology.disk(radius)
        ) for i in ori_img
    )

    return np.array(wv_bg)
    
def wrap_subtract_bg(img, selem=None):
    if selem is None: return img
    dtype = img.dtype
    assert np.issubdtype(dtype, np.integer), (
        'image pixel dtype needs to be integer to perform local'
        ' background subtraction'
    )
    d_info = np.iinfo(dtype)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        bg = skimage.filters.rank.mean_percentile(
            img, p0=0, p1=0.25, selem=selem
        )
    img = np.clip(img.astype(int) - bg.astype(int), d_info.min, d_info.max)
    return img.astype(dtype)

def wrap_rescale_intensity(img, rescale_min, rescale_max):
    img = skimage.exposure.rescale_intensity(
        img.astype(float), 
        in_range=(rescale_min, rescale_max), 
        out_range=(0, 0.983)
    )
    return img

def wrap_resize(img, size):
    if ~np.all(img.shape == size):
        img = skimage.transform.resize(img.astype(float), size, order=3)
    return skimage.img_as_ubyte(img)

def process(
    img_path, channel,
    out_dir, out_name,
    pixel_scale, subtract_bg=False,
    rescale_p0=5, rescale_p1=99.999,
    block_size=2000, block_overlap=200,
    adjust_gamma_value=None
):

    start_time = int(time.perf_counter())

    input_file_path = img_path
    nucleus_channel = channel
    output_dir = out_dir
    output_name = out_name
    scale = pixel_scale
    block_size = block_size
    local_bg_selem = skimage.morphology.disk(50)

    output_path = (
        pathlib.Path(output_dir) / output_name / 'unmicst2' / '{}_Probabilities_{}.tif'.format(
            output_name, nucleus_channel
        )
    )

    img = skimage.io.imread(input_file_path, key=nucleus_channel)
    dtype = img.dtype
    # img = np.log1p(img)

    # rescale_min = img.min()
    # rescale_max = np.percentile(img, 99.9999)

    wv_settings = rowit.WindowView(
        # img.shape, block_size=10000, overlap_size=1000,
        img.shape, block_size=block_size, overlap_size=block_overlap
    )
    img_wv = wv_settings.window_view_list(img)


    img_wv = Parallel(n_jobs=-1, verbose=1)(delayed(wrap_rescale)(
        i, scale, kwargs=dict(order=3, preserve_range=True)
    ) for i in img_wv)

    img_wv = wrap_round_dtype(img_wv, dtype)

    if adjust_gamma_value is not None:
        img_wv = skimage.exposure.adjust_gamma(
            img_wv, adjust_gamma_value
        )
    
    if subtract_bg == True:
        img_wv = Parallel(n_jobs=-1, verbose=1, max_nbytes=None)(delayed(wrap_subtract_bg)(
            i, local_bg_selem
        ) for i in img_wv)

    rescale_min = np.percentile(np.array(img_wv).flatten(), rescale_p0)
    rescale_max = np.percentile(np.array(img_wv).flatten(), rescale_p1)
    img_wv = Parallel(n_jobs=-1, verbose=1)(delayed(wrap_rescale_intensity)(
        i, rescale_min, rescale_max
    ) for i in img_wv)

    for idx, class_i in enumerate(range(3)[::-1]):
        prob_wv = [
            UnMicst2.UNet2D.singleImageInference(np.array([i, i]), 'accumulate', class_i)
            for i in img_wv
        ]
        prob_wv = Parallel(n_jobs=-1, verbose=1)(delayed(wrap_resize)(
            i, (block_size, block_size)
        ) for i in prob_wv)
        prob_wv = wv_settings.reconstruct(np.array(prob_wv))
        pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        append = False if idx == 0 else True
        save_kwargs = dict(
            bigtiff=True, 
            photometric='minisblack', 
            resolution=(0.325, 0.325),
            tile=(1024, 1024),
            metadata=None,
            check_contrast=False
        )
        skimage.io.imsave(str(output_path), prob_wv, append=append, **save_kwargs)
        if idx == 1:
            preview_name = output_path.name.replace(
                f'_Probabilities_{nucleus_channel}.tif',
                f'_Preview_{nucleus_channel}.tif'
            )
            preview_path = output_path.parent / preview_name
            skimage.io.imsave(str(preview_path), prob_wv, append=False, **save_kwargs)
        if class_i == 0:
            img_wv = Parallel(n_jobs=-1, verbose=1)(delayed(wrap_resize)(
                i, (block_size, block_size)
            ) for i in img_wv)
            img_wv = wv_settings.reconstruct(np.array(img_wv))
            skimage.io.imsave(str(preview_path), img_wv, append=True, **save_kwargs)

    end_time = int(time.perf_counter())
    print('elapsed', datetime.timedelta(seconds=end_time-start_time))


import pathlib
import csv
import sys
import argparse
import tifffile
import time, datetime


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        metavar='config-csv',
        required=True
    )
    args = parser.parse_args(argv[1:])
    

    model_path = pathlib.Path('/home/ychen/mcmicro/UnMicst/models/nucleiDAPILAMIN')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        UnMicst2.UNet2D.singleImageInferenceSetup(model_path, 0, -1, -1)


    def process_arg_path(path):
        path = pathlib.Path(path)
        if path.suffix == '.csv':
            with open(path) as file_config_csv:
                csv_reader = csv.DictReader(file_config_csv)
                return sanitize_config([dict(row) for row in csv_reader])
        ometiff = sorted(path.glob('*.ome.tiff'))
        if len(ometiff) == 0:
            ometiff = sorted(path.glob('*.ome.tif'))
        if len(ometiff) == 0:
            print(f"no .ome.tiff or .ome.tif found in {path}")
            return
        return [{'path': pp} for pp in ometiff]
    

    def sanitize_config(config):
        for idx, cc in enumerate(config):
            for key, value in cc.items():
                assert value is not None, (
                    f"{key} column does not have a value at row {idx+1}"
                )
        return config
    

    def set_config_defaults(config):
        assert 'path' in config, 'must at least contain path to ome-tiff'
        path = pathlib.Path(config['path'])
        return {
            'path': path,
            'name': config.get('name', path.stem.replace('.ome', '')),
            'out_dir': pathlib.Path(config.get('out_dir', path.parent))
        }


    def to_log(log_path, img_path, time_diff, kwargs):
        img_path = pathlib.Path(img_path)
        with tifffile.TiffFile(img_path) as tif:
            shape = tif.series[0].shape
        arg_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
        with open(log_path, 'a') as log_file:
            log_file.write(
                f"{datetime.timedelta(seconds=time_diff)} | {img_path.name} | {shape} | {arg_str}\n"
            )

    file_config = process_arg_path(args.c)

    for config in file_config[:]:
        config = set_config_defaults(config)
        print('Processing', config['name'])
        start_time = int(time.perf_counter())
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            kwargs = dict(
                img_path=str(config['path']),
                channel=0,
                out_dir=config['out_dir'], 
                out_name=config['name'],
                pixel_scale=0.325/0.65,
                subtract_bg=False,
                rescale_p0=5, rescale_p1=100,
                block_size=5000, block_overlap=200,
                adjust_gamma_value=0.8
            )
            process(**kwargs)
        end_time = int(time.perf_counter())
        to_log('/mnt/orion/Mercury-3/20230106/unmicst.log', config['path'], end_time-start_time, kwargs)
        print()

    UnMicst2.UNet2D.singleImageInferenceCleanup()

    return 0


if __name__ == '__main__':
    sys.exit(main())