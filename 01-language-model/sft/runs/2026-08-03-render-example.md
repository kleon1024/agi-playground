# One real no_robots record through the real loss mask

`README.md`'s `render_and_mask` walkthrough uses a hypothetical three-token
turn ("yes."). This run replaces "hypothetical" with "actual": one real row
of `HuggingFaceH4/no_robots`, rendered by the unmodified `render_and_mask`
this stage trains with, with its real per-token loss mask printed out.

## Command

```bash
# regenerate the HF-format export of this repo's own tokenizer (not checked
# into git, same as ckpt.pt — see ../../01-tokenizer/README.md)
python ../../01-tokenizer/prod/hf_tokenizer.py export \
    ../../01-tokenizer/tokenizer.json tokenizer_hf.json \
    --corpus <any real text corpus, for the export-fidelity check only>

cd ../core
python render_example.py --tokenizer ../../01-tokenizer/tokenizer_hf.json \
    --out ../runs/2026-08-03-render-example.md
```

`render_example.py` calls `_rows` and `render_and_mask` from `sft.py`
directly — no dataset loading or masking logic is reimplemented here. It
scans `HuggingFaceH4/no_robots`'s `train` split in order for the first
two-turn (user, assistant) row that renders to between 20 and 45 tokens (a
size window chosen only so the table below fits in a README; not by content
or mask ratio) and stops at the first match, row **137**.

## Software

torch 2.13.0, tokenizers 0.23.1, datasets 5.0.1 (uv-managed local venv, CPU
only — no GPU is needed to render and mask one record).

## The record

category: `'Open QA'`

- user: `'What was Phish’s last studio album?'`
- assistant: `'Phish’s most recent album was “Sigma Oasis”, which was released on April 2nd of 2020.'`

45 tokens total, 24 trained (labels != -100), **53.3%** of this record's
tokens.

```
  i  token id  decoded token        label
  0     16385  '<|im_start|>'       -100
  1     11336  'user'               -100
  2        10  '\n'                 -100
  3      1889  'What'               -100
  4       399  ' was'               -100
  5      1393  ' Ph'                -100
  6       554  'ish'                -100
  7       504  '’s'                 -100
  8      1421  ' last'              -100
  9       600  ' stud'              -100
 10       995  'io'                 -100
 11     13502  ' alb'               -100
 12       384  'um'                 -100
 13        63  '?'                  -100
 14     16386  '<|im_end|>'         -100
 15        10  '\n'                 -100
 16     16385  '<|im_start|>'       -100
 17       557  'ass'                -100
 18      8697  'istant'             -100
 19        10  '\n'                 -100
 20      4195  'Ph'                 Ph
 21       554  'ish'                ish
 22       504  '’s'                 ’s
 23       684  ' most'               most
 24      2342  ' recent'             recent
 25     13502  ' alb'                alb
 26       384  'um'                 um
 27       399  ' was'                was
 28       578  ' “'                  “
 29        83  'S'                  S
 30     13500  'igma'               igma
 31       469  ' O'                  O
 32     12038  'asis'               asis
 33      5334  '”,'                 ”,
 34       482  ' which'              which
 35       399  ' was'                was
 36      4159  ' released'           released
 37       332  ' on'                 on
 38      3172  ' April'              April
 39      9180  ' 2nd'                2nd
 40       276  ' of'                 of
 41     11231  ' 2020'               2020
 42        46  '.'                  .
 43     16386  '<|im_end|>'         <|im_end|>
 44        10  '\n'                 -100
```
