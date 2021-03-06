"""
Research question:
is the connection between a nouns-next word P less lexically specific (higher conditional entropy) in p1 vs p2?
if so, this would support the idea that nouns are learned more compactly/flexibly in p1?

conditional entropy (x | y) = how much more information I need to figure out what X is when Y is known.

so if y is the probability distribution of next-words, and x is P over nouns,
 the hypothesis is that conditional entropy is higher in partition 1 vs. 2

"""

from pyitlib import discrete_random_variable as drv
from numpy.lib.stride_tricks import as_strided
import numpy as np
import matplotlib.pyplot as plt

from categoryeval.ba import BAScorer
from preppy import FlexiblePrep
from preppy.docs import load_docs

from provident import configs


CORPUS_NAME = 'newsela'  # 'childes-20191112'
NUM_TYPES = 4096 * 4 if CORPUS_NAME == 'newsela' else 4096  # x8 is suitable for newsela
PROBES_NAME = 'sem-4096'

NUM_TICKS = 4
AX_FONT_SIZE = 14

corpus_path = configs.Dirs.corpora / f'{CORPUS_NAME}.txt'
train_docs, _ = load_docs(corpus_path)

prep = FlexiblePrep(train_docs,
                    reverse=False,
                    sliding=False,
                    num_types=NUM_TYPES,
                    num_parts=2,
                    num_iterations=(20, 20),
                    batch_size=64,
                    context_size=7,
                    num_evaluations=20,
                    )

ba_scorer = BAScorer(CORPUS_NAME,
                     probes_names=[PROBES_NAME],
                     w2id=prep.store.w2id)

if PROBES_NAME == 'sem-4096':
    probes = ba_scorer.name2store[PROBES_NAME].types
else:
    probes = ba_scorer.name2store[PROBES_NAME].cat2probes[PROBES_NAME]
print(f'num probes={len(probes)}')


# windows
token_ids_array = np.array(prep.store.token_ids, dtype=np.int64)
num_possible_windows = len(token_ids_array) - prep.num_tokens_in_window
shape = (num_possible_windows, prep.num_tokens_in_window)
windows = as_strided(token_ids_array, shape, strides=(8, 8), writeable=False)
print(f'Matrix containing all windows has shape={windows.shape}')

num_windows_list = [int(i) for i in np.linspace(0, len(windows), NUM_TICKS + 1)][1:]


def collect_data(windows, reverse: bool):

    if reverse:
        windows = np.flip(windows, 0)

    ce = []
    for num_windows in num_windows_list:

        ws = windows[:num_windows]
        print(num_windows, ws.shape)

        # probe windows
        row_ids = np.isin(ws[:, -2], [prep.store.w2id[w] for w in probes])
        probe_windows = ws[row_ids]
        print(f'num probe windows={len(probe_windows)}')

        x = probe_windows[:, -2]  # CAT member
        y = probe_windows[:, -1]  # next-word

        cei = drv.entropy_conditional(x, y)

        print(f'ce={cei}')
        print()
        ce.append(cei)

    return ce


# collect data
y1 = collect_data(windows, reverse=False)
y2 = collect_data(windows, reverse=True)

fig, ax = plt.subplots(1, figsize=(6, 4), dpi=None)
plt.title('', fontsize=AX_FONT_SIZE)
ax.set_ylabel(f'H({PROBES_NAME}|next word)', fontsize=AX_FONT_SIZE)
ax.set_xlabel(f'{CORPUS_NAME.title()} Cumulative Number of Tokens', fontsize=AX_FONT_SIZE)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.tick_params(axis='both', which='both', top=False, right=False)
ax.plot(num_windows_list, y1, '-', linewidth=2, color='C0', label='simple first')
ax.plot(num_windows_list, y2, '-', linewidth=2, color='C1', label='complex first')
plt.legend(frameon=False, fontsize=AX_FONT_SIZE, loc='lower right')
plt.tight_layout()
plt.show()



