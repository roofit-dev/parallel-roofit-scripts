/**
 * Run debug with root as executable, arguments:
 *   -l -b simple/vbf.root
 * and working directory:
 *   ~/projects/apcocsm/carsten
 */

// remove INFO stream to keep output clean
RooMsgService::instance().deleteStream(1);

void test(bool timeEP, int numcpu, bool timeZtautauCR, bool timeSR, bool timeTopCR) {
  RooTimer::set_time_evaluate_partition(timeEP);

  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Eval), RooFit::ClassName("RooNLLVar"));

  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
  RooAbsPdf* pdf = mc->GetPdf();
  RooAbsData * data = w->data("obsData");
  RooAbsReal* nll = pdf->createNLL(*data, RooFit::NumCPU(numcpu, 0));

  RooAddition * ADDnll = dynamic_cast<RooAddition*>(nll);

  // actual nll
  // RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(&ADDnll->list()[0]) // dangerous: works in this case, but direct indexing can lead to segfault
  RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(ADDnll->list().at(0));

  NLLnll->setTimeEvaluatePartition("ZtautauCR", timeZtautauCR);
  NLLnll->setTimeEvaluatePartition("SR", timeSR);
  NLLnll->setTimeEvaluatePartition("TopCR", timeTopCR);

  NLLnll->getValV();
}

test(true, 1, true, true, true);
test(true, 1, false, false, false);
test(false, 1, true, true, true);
test(false, 1, true, true, false);
test(false, 1, true, false, true);
test(false, 1, false, true, true);
test(false, 1, true, false, false);
test(false, 1, false, true, false);
test(false, 1, false, false, true);
test(false, 1, false, false, false);

test(true, 2, true, true, true);
test(true, 2, false, false, false);
test(false, 2, true, true, true);
test(false, 2, true, true, false);
test(false, 2, true, false, true);
test(false, 2, false, true, true);
test(false, 2, true, false, false);
test(false, 2, false, true, false);
test(false, 2, false, false, true);
test(false, 2, false, false, false);

// NLLnll->setValueDirty()
// NLLnll->setShapeDirty()

