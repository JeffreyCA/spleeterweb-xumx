# Copyright (c) 2021 Sony Corporation. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import warnings
import norbert
import scipy.signal
import resampy
import soundfile as sf
import numpy as np
import nnabla as nn
from nnabla.ext_utils import get_extension_context
from .args import get_inference_args
from .model import *


def istft(X, rate=44100, n_fft=4096, n_hopsize=1024):
    _, audio = scipy.signal.istft(
        X / (n_fft // 2),
        rate,
        nperseg=n_fft,
        noverlap=n_fft - n_hopsize,
        boundary=True
    )
    return audio


def separate(
    audio,
    model_path='models/x-umx.h5',
    niter=1,
    softmask=False,
    alpha=1.0,
    residual_model=False
):
    """
    Performing the separation on audio input
    Parameters
    ----------
    audio: np.ndarray [shape=(nb_samples, nb_channels, nb_timesteps)]
        mixture audio
    model_path: str
        path to model folder, defaults to `models/`
    niter: int
         Number of EM steps for refining initial estimates in a
         post-processing stage, defaults to 1.
    softmask: boolean
        if activated, then the initial estimates for the sources will
        be obtained through a ratio mask of the mixture STFT, and not
        by using the default behavior of reconstructing waveforms
        by using the mixture phase, defaults to False
    alpha: float
        changes the exponent to use for building ratio masks, defaults to 1.0
    residual_model: boolean
        computes a residual target, for custom separation scenarios
        when not all targets are available, defaults to False
    Returns
    -------
    estimates: `dict` [`str`, `np.ndarray`]
        dictionary of all restimates as performed by the separation model.
    """
    # convert numpy audio to NNabla Variable
    audio_nn = nn.Variable.from_numpy_array(audio.T[None, ...])
    source_names = []
    V = []

    sources = ['bass', 'drums', 'vocals', 'other']
    for j, target in enumerate(sources):
        if j == 0:
            unmix_target = OpenUnmix_CrossNet(max_bin=1487)
            unmix_target.is_predict = True
            nn.load_parameters(model_path)
            mix_spec, msk, _ = unmix_target(audio_nn, test=True)
        Vj = msk[Ellipsis, j*2:j*2+2, :] * mix_spec
        if softmask:
            # only exponentiate the model if we use softmask
            Vj = Vj**alpha
        # output is nb_frames, nb_samples, nb_channels, nb_bins
        V.append(Vj.d[:, 0, ...])  # remove sample dim
        source_names += [target]
    V = np.transpose(np.array(V), (1, 3, 2, 0))

    real, imag = STFT(audio_nn, center=True)

    # convert to complex numpy type
    X = real.d + imag.d*1j
    X = X[0].transpose(2, 1, 0)

    if residual_model or len(sources) == 1:
        V = norbert.residual_model(V, X, alpha if softmask else 1)
        source_names += (['residual'] if len(sources) > 1
                         else ['accompaniment'])

    Y = norbert.wiener(V, X.astype(np.complex128), niter,
                       use_softmask=softmask)

    estimates = {}
    for j, name in enumerate(source_names):
        audio_hat = istft(
            Y[..., j].T,
            n_fft=unmix_target.n_fft,
            n_hopsize=unmix_target.n_hop
        )
        estimates[name] = audio_hat.T

    return estimates


def test():
    args = get_inference_args()

    # Set NNabla context and Dynamic graph execution
    ctx = get_extension_context(args.context)
    nn.set_default_context(ctx)

    # Enable the NNabla Dynamic excecution
    nn.set_auto_forward(True)

    for input_file in args.inputs:
        # handling an input audio path
        info = sf.info(input_file)
        start = int(args.start * info.samplerate)
        # check if dur is none
        if args.duration > 0:
            # stop in soundfile is calc in samples, not seconds
            stop = start + int(args.duration * info.samplerate)
        else:
            # set to None for reading complete file
            stop = None

        audio, rate = sf.read(
            input_file,
            always_2d=True,
            start=start,
            stop=stop
        )

        if audio.shape[1] > 2:
            warnings.warn(
                'Channel count > 2! '
                'Only the first two channels will be processed!')
            audio = audio[:, :2]

        if rate != args.sample_rate:
            # resample to model samplerate if needed
            audio = resampy.resample(audio, rate, args.sample_rate, axis=0)

        if audio.shape[1] == 1:
            # if we have mono, let's duplicate it
            # as the input of OpenUnmix is always stereo
            audio = np.repeat(audio, 2, axis=1)

        estimates = separate(
            audio,
            model_path=args.model,
            niter=args.niter,
            alpha=args.alpha,
            softmask=args.softmask,
            residual_model=args.residual_model
        )

        if not args.outdir:
            model_path = Path(args.model)
            if not model_path.exists():
                output_path = Path(Path(input_file).stem + '_' + model)
            else:
                output_path = Path(
                    Path(input_file).stem + '_' + model_path.stem
                )
        else:
            if len(args.inputs) > 1:
                output_path = Path(args.outdir) / Path(input_file).stem
            else:
                output_path = Path(args.outdir)

        output_path.mkdir(exist_ok=True, parents=True)

        for target, estimate in estimates.items():
            sf.write(
                str(output_path / Path(target).with_suffix('.wav')),
                estimate,
                args.sample_rate
            )


if __name__ == '__main__':
    test()
