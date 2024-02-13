#!/bin/bash
##
# Generates space tokenized alignments to work with OpusTrainer Tags
#

set -x
set -euo pipefail

echo "###### Generating alignments"
test -v BIN
test -v SRC
test -v TRG

corpus_prefix=$1
output_prefix=$2

COMPRESSION_CMD="${COMPRESSION_CMD:-pigz}"
ARTIFACT_EXT="${ARTIFACT_EXT:-gz}"

cd "$(dirname "${0}")"

output_dir=$(dirname "${output_prefix}")
mkdir -p "${output_dir}"
dir="${output_dir}/tmp"
mkdir -p "${dir}"

echo "### Creating merged corpus"
test -s "${output_prefix}.aln.${ARTIFACT_EXT}" || test -s "${dir}/corpus" ||
  paste <(${COMPRESSION_CMD} -dc "${corpus_prefix}.${SRC}.${ARTIFACT_EXT}") <(${COMPRESSION_CMD} -dc "${corpus_prefix}.${TRG}.${ARTIFACT_EXT}") |
  sed 's/\t/ ||| /' >"${dir}/corpus"

echo "### Training alignments"
test -s "${output_prefix}.aln.${ARTIFACT_EXT}" || test -s "${dir}/align.s2t.${ARTIFACT_EXT}" ||
  "${BIN}/fast_align" -vod -i "${dir}/corpus" |
  ${COMPRESSION_CMD} >"${dir}/align.s2t.${ARTIFACT_EXT}"
test -s "${output_prefix}.aln.${ARTIFACT_EXT}" || test -s "${dir}/align.t2s.${ARTIFACT_EXT}" ||
  "${BIN}/fast_align" -vodr -i "${dir}/corpus" |
  ${COMPRESSION_CMD} >"${dir}/align.t2s.${ARTIFACT_EXT}"

echo "### Symmetrizing alignments"
test -s "${output_prefix}.aln.${ARTIFACT_EXT}" || test -s "${dir}/align.t2s" ||
  ${COMPRESSION_CMD} -d "${dir}/align.s2t.${ARTIFACT_EXT}" "${dir}/align.t2s.${ARTIFACT_EXT}"
test -s "${output_prefix}.aln.${ARTIFACT_EXT}" ||
  "${BIN}/atools" -i "${dir}/align.s2t" -j "${dir}/align.t2s" -c grow-diag-final-and |
  ${COMPRESSION_CMD} >"${output_prefix}.aln.${ARTIFACT_EXT}"


echo "### Deleting tmp dir"
rm -rf "${dir}"

echo "###### Done: Generating alignments"
