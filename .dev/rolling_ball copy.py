import imagej
import numpy as np

import contextlib
import io


def init_ij():
    global ij, BackgroundSubtracter, ImagePlus, bg_subtracter
    if 'ij' in globals(): return

    # initialize imagej
    ij = imagej.init(r"C:\Users\Public\Downloads\pyimagej\Fiji.app")
    # ij = imagej.init('sc.fiji:fiji:2.1.0')
    import jpype
    # get Java class representations
    BackgroundSubtracter = jpype.JClass(
        'ij.plugin.filter.BackgroundSubtracter'
    )
    ImagePlus = jpype.JClass('ij.ImagePlus')
    bg_subtracter = BackgroundSubtracter()
    return

def ij_rolling_ball(img, radius):
    with contextlib.redirect_stdout(io.StringIO()):
        init_ij()

    src_dtype = img.dtype
    src_shape = img.shape

    imp = ij.py.to_java(img)
    imp = ij.dataset().create(imp)
    imp = ij.convert().convert(imp, ImagePlus)

    del img

    bg_subtracter.rollingBallBackground(
        imp.getProcessor(), radius, 
        False, False, False, False, True
    )

    subtracted = np.array(
        imp.getProcessor().getPixels(),
        dtype=src_dtype
    ).reshape(src_shape)

    imp.close()
    return subtracted


def ij_rolling_ball_dask(img, radius, chunk_size=2*11, overlap_factor=2):
    global da
    if 'da' not in globals():
        import dask.array as da
    
    overlap_depth = radius * get_shrink_factor(radius)
    if overlap_depth > min(img.shape):
        print(
            f"Can't get consistent result with current image shape "
            f"{img.shape} and ball radius {radius}, fallback to non-"
            f"parallelized method `ij_rolling_ball`"
        )
        return ij_rolling_ball(img, radius)
    
    img_shape = img.shape
    h_pad, w_pad = overlap_depth - np.remainder(img.shape, chunk_size)
    if h_pad < 0: h_pad = 0
    if w_pad < 0: w_pad = 0
    print(h_pad, w_pad)

    img = np.pad(img, [(0, h_pad), (0, w_pad)], mode='maximum')

    da_img = da.from_array(img, chunks=chunk_size)
    da_result = da.map_overlap(
        ij_rolling_ball, da_img, dtype=img.dtype, 
        depth=overlap_depth, boundary='none', radius=radius
    )

    return da_result.compute()[:img_shape[0], :img_shape[1]]


def get_random_img(shape, dtype=np.uint16):
    random_img = np.random.random(shape) * np.iinfo(dtype).max
    return random_img.astype(dtype)


def get_shrink_factor(radius):
    if radius <= 10:
        shrinkFactor = 2
    elif radius <= 30:
        shrinkFactor = 2
    elif radius <= 100:
        shrinkFactor = 4
    else:
        shrinkFactor = 8
    return shrinkFactor


# rb.test(shape=(1102, 1725), radius=53, overlap_factor=8, chunk_size=2**10)
# rb.test(shape=(1102, 1279), radius=31, overlap_factor=8, chunk_size=2**9)
def test(
    shape=None,
    radius=None,
    overlap_factor=None,
    chunk_size=None,
):
    global plt
    if 'plt' not in globals():
        import matplotlib.pyplot as plt
    if shape is None:
        shape = np.random.randint(1000, 2000, size=2)
    if radius is None:
        radius = np.random.randint(1, 150)
    if overlap_factor is None:
        overlap_factor = get_shrink_factor(radius)
    if chunk_size is None:
        chunk_size = 2**9
    test_img = np.random.randint(
        0, 65535, size=shape,
        dtype=np.uint16
    )
    print(f'shape={test_img.shape}, radius={radius}, overlap_factor={overlap_factor}')
    plt.figure()
    plt.imshow(
        ij_rolling_ball(test_img, radius=radius) !=
        ij_rolling_ball_dask(
            test_img, radius=radius, 
            chunk_size=chunk_size, overlap_factor=overlap_factor,
        )
    )
    plt.suptitle(f'{test_img.shape}; r = {radius}; f = {overlap_factor}')
    