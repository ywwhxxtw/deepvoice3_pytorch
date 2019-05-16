from concurrent.futures import ProcessPoolExecutor
from functools import partial
import numpy as np
import os
import glob
#from util import audio
import audio
from hparams import hparams as hp


def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    '''Preprocesses the THCHS30 dataset from a given input path into a given output directory.

    Args:
      in_dir: The directory where you have downloaded the THCHS30 dataset
      out_dir: The directory to write the output into
      num_workers: Optional number of worker processes to parallelize across
      tqdm: You can optionally pass tqdm to get a nice progress bar

    Returns:
      A list of tuples describing the training examples. This should be written to train.txt
    '''

    # We use ProcessPoolExecutor to parallize across processes. This is just an optimization and you
    # can omit it and just call _process_utterance on each input if you want.
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    index = 1
    wav_path = None

    # trn_files = glob.glob(os.path.join(in_dir, 'biaobei_48000', '*.trn'))
    #
    # for trn in trn_files:
    #   with open(trn) as f:
    #     pinyin = f.readline().strip('\n')
    #     wav_file = trn[:-4] + '.wav'
    #     task = partial(_process_utterance, out_dir, index, wav_file, pinyin)
    #     futures.append(executor.submit(task))
    #     index += 1
    with open(in_dir + '.txt', encoding='utf-8') as f:
      for line in f:
          if index % 2 == 1:
              parts = line.strip().split('\t')
              wav_path = os.path.join(in_dir + '-wav', '%s.wav' % parts[0])
              #print(wav_path)
              if os.path.exists(wav_path) is False:
                  wav_path = None
          else:
              text = line.strip()
              if wav_path is not None and text is not None:
                  task = partial(_process_utterance, out_dir, int(index/2), wav_path, text)
                  futures.append(executor.submit(task))
          index += 1
    return [future.result() for future in tqdm(futures) if future.result() is not None]


def build_from_path_old(hparams, input_dirs, mel_dir, linear_dir, wav_dir, n_jobs=12, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=n_jobs)
    futures = []
    index = 1
    wav_path = None

    with open(input_dirs+'.txt', encoding='utf-8') as f:
        for line in f:
            if index % 2 == 1:
                parts = line.strip().split('\t')
                wav_path = os.path.join(input_dirs+'-wav', '%s.wav' % parts[0])
                if os.path.exists(wav_path) is False:
                    wav_path = None
            else:
                text = line.strip()
                if wav_path is not None and text is not None:
                    print(int(index/2))
                    futures.append(executor.submit(
                        partial(_process_utterance, mel_dir, linear_dir, wav_dir, int(index/2), wav_path, text, hparams)))

            index += 1
    return [future.result() for future in tqdm(futures)]


def _process_utterance(out_dir, index, wav_path, pinyin):
    '''Preprocesses a single utterance audio/text pair.

    This writes the mel and linear scale spectrograms to disk and returns a tuple to write
    to the train.txt file.

    Args:
    out_dir: The directory to write the spectrograms into
    index: The numeric index to use in the spectrogram filenames.
    wav_path: Path to the audio file containing the speech input
    pinyin: The pinyin of Chinese spoken in the input audio file

    Returns:
    A (spectrogram_filename, mel_filename, n_frames, text) tuple to write to train.txt
    '''

    # Load the audio to a numpy array:
    wav = audio.load_wav(wav_path)

    # rescale wav for unified measure for all clips
    wav = wav / np.abs(wav).max() * 0.999

    # trim silence
    wav = audio.trim_silence(wav)

    # Compute the linear-scale spectrogram from the wav:
    spectrogram = audio.spectrogram(wav).astype(np.float32)
    n_frames = spectrogram.shape[1]
    if n_frames > hp.max_frame_num:
        return None

    # Compute a mel-scale spectrogram from the wav:
    mel_spectrogram = audio.melspectrogram(wav).astype(np.float32)

    # Write the spectrograms to disk:
    spectrogram_filename = 'biaobei-spec-%05d.npy' % index
    mel_filename = 'biaobei-mel-%05d.npy' % index
    np.save(os.path.join(out_dir, spectrogram_filename), spectrogram.T, allow_pickle=False)
    np.save(os.path.join(out_dir, mel_filename), mel_spectrogram.T, allow_pickle=False)

    # Return a tuple describing this training example:
    return (spectrogram_filename, mel_filename, n_frames, pinyin)