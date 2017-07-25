/**
 * Run debug with root as executable, arguments:
 *   -l -b simple/vbf.root setEvalPartTimingsViaMPFE.cpp
 * and working directory:
 *   ~/projects/apcocsm/carsten
 */

using namespace RooFit;


void test(bool timeEP, int numcpu, bool timeZtautauCR, bool timeSR, bool timeTopCR, bool dynamic_test=false) {
  std::cout << "\n START TEST: " << timeEP << " " << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;

  RooTimer::set_time_evaluate_partition(timeEP);

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

  if (dynamic_test) {
    auto params = NLLnll->getParameters(data);
    auto piter = params->fwdIterator();
    auto param_0 = piter.next();

    std::cout << std::endl << "switch" << std::endl;
    dynamic_cast<RooRealVar*>(param_0)->setVal(2);
    RooTimer::set_time_evaluate_partition(!timeEP);
    NLLnll->setTimeEvaluatePartition("ZtautauCR", !timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", !timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", !timeTopCR);

    NLLnll->getValV();

    std::cout << std::endl << "switch back" << std::endl;
    dynamic_cast<RooRealVar*>(param_0)->setVal(0);
    RooTimer::set_time_evaluate_partition(timeEP);
    NLLnll->setTimeEvaluatePartition("ZtautauCR", timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", timeTopCR);

    NLLnll->getValV();
  }

  std::cout << "\n END TEST: " << timeEP << " " << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;
}

void setEvalPartTimingsViaMPFE() {
  // remove INFO stream to keep output clean
  RooMsgService::instance().deleteStream(1);
  // add relevant DEBUG streams
  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Eval), RooFit::ClassName("RooNLLVar"));
  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Optimization), RooFit::ClassName("RooAbsTestStatistic"), RooFit::ClassName("RooNLLVar"));

  std::cout << "\n\n --- SINGLE CORE TESTS --- \n" << std::endl;
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

  std::cout << "\n\n --- MULTI CORE TESTS --- \n" << std::endl;
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

  std::cout << "\n\n --- DYNAMIC TIMING SWITCH TESTS --- \n" << std::endl;
  test(true, 1, true, true, true, true);
  test(false, 1, false, false, false, true);
  test(false, 1, true, false, false, true);
  test(true, 1, true, false, false, true);
  test(true, 2, true, true, true, true);
  test(false, 2, false, false, false, true);
  test(false, 2, true, false, false, true);
  test(true, 2, true, false, false, true);
}
