#!/usr/bin/env zsh
filename=2cpu_timing1_rep0.txt

grep "RooNLLVar::evaluatePartition.*init-stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 0.383575
grep "RooNLLVar::evaluatePartition.*recalculateCache" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 1.68669

grep "RooNLLVar::evaluatePartition.*binnedPdf, data->get(i)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 1.44702
grep "RooNLLVar::evaluatePartition.*binnedPdf, data->is valid" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 2.00974
grep "RooNLLVar::evaluatePartition.*binnedPdf, data->weight()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 2.54615
grep "RooNLLVar::evaluatePartition.*binnedPdf, _binnedPdf->getVal()\*_binw\[i\]" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 9.14036
grep "RooNLLVar::evaluatePartition.*binnedPdf, result calculation" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 9.78787

# check for not-binnedPdf output:
grep "RooNLLVar::evaluatePartition.*not-binnedPdf" $filename | wc


grep "RooNLLVar::evaluatePartition.*not-binnedPdf, data->get(i)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, data->is valid" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, data->weight()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, data->weight squared stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, -eventWeight * pdfClone->getLogVal(_normSet)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, kahan sum weight and result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 

grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, data->get(i)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, data->weightSquared()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, rest of kahan sum weight" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, expectedEvents" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, data->sumEntries()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, expectedW2 - sumW2*log(expected)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term, kahan sum result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 
grep "RooNLLVar::evaluatePartition.*not-binnedPdf, extended term not weightSq, kahan sum result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 


grep "RooNLLVar::evaluatePartition.*simCount>1, kahan sum result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 11.7412
grep "RooNLLVar::evaluatePartition.*first, wire all caches" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# 0.018935
grep "RooNLLVar::evaluatePartition.*doOffset, kahan subtract result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
# n.a.
