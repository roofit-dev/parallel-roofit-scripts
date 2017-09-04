#!/usr/bin/env zsh
filename=$1
shift
pids=$@
awk_sum='{s+=$1}END{print s}'
awk_median='{ count[NR] = $1; } END { if (NR % 2) { print count[(NR + 1) / 2]; } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; } }'

# total
for pid in $@; do
        echo "pid: ${pid}"

        grep "RooRealSumPdf::evaluate.*pid${pid}.*fwdIterators" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooRealSumPdf::evaluate.*pid${pid}.*while iteration" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*funcIter\.next" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coef->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, func->isSelectedComp(), wall" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, coef->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, funcIter\.next()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, func->isSelectedComp(), wall" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'

        grep "RooRealSumPdf::evaluate.*pid${pid}.*finishing stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}'
done

# median
for pid in $@; do
        echo "pid: ${pid}"

        grep "RooRealSumPdf::evaluate.*pid${pid}.*fwdIterators" $filename | sed 's/.*cpu \(.*\)s/\1/' | sort -g | awk $awk_median

        grep "RooRealSumPdf::evaluate.*pid${pid}.*while iteration" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median

        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*funcIter\.next" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coef->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, func->isSelectedComp(), wall" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\..*coefVal, coef->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median

        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, funcIter\.next()" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, func->isSelectedComp(), wall" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
        grep "RooRealSumPdf::evaluate.*pid${pid}.*!haveLastCoef, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median

        grep "RooRealSumPdf::evaluate.*pid${pid}.*finishing stuff" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk $awk_median
done


# results:
# ../../vbfComb_detailedRRealSumPdfEvaluate_analyze_txt.sh 2cpu_timing1_rep0.txt 21005 21006
# pid: 21005
# 0.003829
# 0.043114
# 0.041853
# 0.101196
# 0.051071
# 2.35513
# 0.050087
# -
# -
# -
# 0.004905
# pid: 21006
# 0.00738
# 0.080763
# 0.078857
# 0.176255
# 0.090976
# 2.66117
# 0.086917
# -
# -
# -
# 0.007758
# pid: 21005
# 1e-06
# 0
# 0
# 0
# 0
# 4.4e-05
# 0
# 0
# 0
# 0
# 2e-06
# pid: 21006
# 1e-06
# 5e-07
# 1.5e-06
# ... etc
# 


# ../../vbfComb_detailedRRealSumPdfEvaluate_analyze_txt.sh 1cpu_timing1_rep0.txt 21280
# pid: 21280
# 0.008789
# 0.093832
# 0.090134
# 0.194567
# 0.089051
# 2.55175
# 0.10042
# -
# -
# - 
# 0.009292


# different functions separately
for iteration in 4 10 16 22 28 34 40 46 52 58 64; do
echo "$iteration: $(grep "RooRealSumPdf::evaluate.*pid${pid}.*wh\.it\.${iteration}.*coefVal, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}')"
done

# 2cpu_timing1_rep0
# PID: 21005
# 4: 0.803995
# 10: 0.263626
# 16: 0.426843
# 22: 0.043596
# 28: 0.392708
# 34: 0.29372
# 40: 0.042666
# 46: 0.383521
# 52: 0.040785
# 58: 0.054277
# 64: 0.035577
# PID: 21006
# 4: 0.909917
# 10: 0.289001
# 16: 0.446216
# 22: 0.072029
# 28: 0.420735
# 34: 0.306762
# 40: 0.071434
# 46: 0.407175
# 52: 0.068836
# 58: 0.085908
# 64: 0.061762
 
# 1cpu_timing1_rep0
# 4: 0.843614
# 10: 0.282509
# 16: 0.42317
# 22: 0.071407
# 28: 0.41868
# 34: 0.298429
# 40: 0.072966
# 46: 0.377297
# 52: 0.069736
# 58: 0.08149
# 64: 0.062719

# only the SR_model
for iteration in 4 10 16 22 28 34 40 46 52 58 64; do
echo "$iteration: $(grep "RooRealSumPdf::evaluate(SR_model.*pid${pid}.*wh\.it\.${iteration}.*coefVal, func->isSelectedComp(), func->getVal" $filename | sed 's/.*cpu \(.*\)s/\1/' | awk '{s+=$1}END{print s}')"
done

# 2cpu_timing1_rep0
# PID 21005
# exactly the same as above, that one only does SR_model.

# PID 21006
# 4: 0.811043
# 10: 0.259336
# 16: 0.417356
# 22: 0.043779
# 28: 0.389557
# 34: 0.290544
# 40: 0.042821
# 46: 0.379254
# 52: 0.041218
# 58: 0.053672
# 64: 0.033625

# 1cpu_timing1_rep0
# 4: 0.762269
# 10: 0.258268
# 16: 0.399238
# 22: 0.047754
# 28: 0.392285
# 34: 0.284881
# 40: 0.047689
# 46: 0.352735
# 52: 0.046243
# 58: 0.054351
# 64: 0.038515

