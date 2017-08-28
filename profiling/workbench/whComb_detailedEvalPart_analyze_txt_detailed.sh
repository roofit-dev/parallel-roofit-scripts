#!/usr/bin/env zsh
filename=2cpu_timing1_rep0.txt

# total
for pid in 69924 69925; do
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*init-stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*recalculateCache" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->get(i)" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->is valid" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->weight()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, _binnedPdf->getVal()\*_binw\[i\]" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, -1\*(-mu + N\*log(mu) - TMath::LnGamma(N+1))" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, result calculation" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooNLLVar::evaluatePartition.*pid${pid}.*simCount>1, kahan sum result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*first, wire all caches" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*doOffset, kahan subtract result" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
done

# median
for pid in 69924 69925; do
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*init-stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*recalculateCache" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'

        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->get(i)" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->is valid" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, data->weight()" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, _binnedPdf->getVal()\*_binw\[i\]" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, -1\*(-mu + N\*log(mu) - TMath::LnGamma(N+1))" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*binnedPdf, result calculation" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'

        grep "RooNLLVar::evaluatePartition.*pid${pid}.*simCount>1, kahan sum result" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*first, wire all caches" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
        grep "RooNLLVar::evaluatePartition.*pid${pid}.*doOffset, kahan subtract result" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk '{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'
done


