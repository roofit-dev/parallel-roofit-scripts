/**
 * Run debug with root as executable, arguments:
 *   -l -b simple/vbf.root setEvalPartTimingsViaMPFE.cpp
 * and working directory:
 *   ~/projects/apcocsm/carsten
 */

using namespace RooFit;


void test(bool timeEPglobal, int numcpu, bool timeZtautauCR, bool timeSR, bool timeTopCR, bool dynamic_test=false) {
  std::cout << "\n START TEST: " << timeEPglobal << " " << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;

  RooTimer::set_time_evaluate_partition(timeEPglobal);

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
    RooTimer::set_time_evaluate_partition(!timeEPglobal);
    NLLnll->setTimeEvaluatePartition("ZtautauCR", !timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", !timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", !timeTopCR);

    NLLnll->getValV();

    std::cout << std::endl << "switch back" << std::endl;
    dynamic_cast<RooRealVar*>(param_0)->setVal(0);
    RooTimer::set_time_evaluate_partition(timeEPglobal);
    NLLnll->setTimeEvaluatePartition("ZtautauCR", timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", timeTopCR);

    NLLnll->getValV();
  }

  std::cout << "\n END TEST: " << timeEPglobal << " " << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;
}

void test2(bool timeEPallComps, bool timeEPallComps_before, int numcpu, bool timeZtautauCR, bool timeSR, bool timeTopCR, bool dynamic_test=false) {
  std::cout << "\n START TEST: " << timeEPallComps << " (before: " << timeEPallComps_before << ") cpu:" << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;

  RooTimer::set_time_evaluate_partition(kFALSE);

  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
  RooAbsPdf* pdf = mc->GetPdf();
  RooAbsData * data = w->data("obsData");
  RooAbsReal* nll = pdf->createNLL(*data, RooFit::NumCPU(numcpu, 0));

  RooAddition * ADDnll = dynamic_cast<RooAddition*>(nll);

  // actual nll
  // RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(&ADDnll->list()[0]) // dangerous: works in this case, but direct indexing can lead to segfault
  RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(ADDnll->list().at(0));

  if (timeEPallComps_before) {
    NLLnll->setTimeEvaluatePartition(timeEPallComps);
  }
  NLLnll->setTimeEvaluatePartition("ZtautauCR", timeZtautauCR);
  NLLnll->setTimeEvaluatePartition("SR", timeSR);
  NLLnll->setTimeEvaluatePartition("TopCR", timeTopCR);
  if (!timeEPallComps_before) {
    NLLnll->setTimeEvaluatePartition(timeEPallComps);
  }

  NLLnll->getValV();

  if (dynamic_test) {
    auto params = NLLnll->getParameters(data);
    auto piter = params->fwdIterator();
    auto param_0 = piter.next();

    std::cout << std::endl << "switch" << std::endl;
    dynamic_cast<RooRealVar*>(param_0)->setVal(2);
    if (timeEPallComps_before) {
      NLLnll->setTimeEvaluatePartition(!timeEPallComps);
    }
    NLLnll->setTimeEvaluatePartition("ZtautauCR", !timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", !timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", !timeTopCR);
    if (!timeEPallComps_before) {
      NLLnll->setTimeEvaluatePartition(!timeEPallComps);
    }

    NLLnll->getValV();

    std::cout << std::endl << "switch back" << std::endl;
    dynamic_cast<RooRealVar*>(param_0)->setVal(0);
    if (timeEPallComps_before) {
      NLLnll->setTimeEvaluatePartition(timeEPallComps);
    }
    NLLnll->setTimeEvaluatePartition("ZtautauCR", timeZtautauCR);
    NLLnll->setTimeEvaluatePartition("SR", timeSR);
    NLLnll->setTimeEvaluatePartition("TopCR", timeTopCR);
    if (!timeEPallComps_before) {
      NLLnll->setTimeEvaluatePartition(timeEPallComps);
    }

    NLLnll->getValV();
  }

  std::cout << "\n END TEST: " << timeEPallComps << " (before: " << timeEPallComps_before << ") cpu:" << numcpu << " " << timeZtautauCR << " " << timeSR << " " << timeTopCR << " " << dynamic_test << "\n" << std::endl;
}


void setEvalPartTimingsViaMPFE() {
  // remove INFO stream to keep output clean
  RooMsgService::instance().deleteStream(1);
  // add relevant DEBUG streams
  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Eval), RooFit::ClassName("RooNLLVar"));
  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Optimization), RooFit::ClassName("RooAbsTestStatistic"), RooFit::ClassName("RooNLLVar"));

  std::cout << "\n\n ----- TEST I: USING GLOBAL ROOTIMER FLAG ----- \n" << std::endl;

  std::cout << "\n\n --- SINGLE CORE TESTS --- \n" << std::endl;
  test(true, 1, true, true, true);
  test(true, 1, false, false, false);
  test(false, 1, true, true, true);
  test(false, 1, true, false, true);
  test(false, 1, false, true, false);
  test(false, 1, false, false, false);

  std::cout << "\n\n --- DUAL CORE TESTS --- \n" << std::endl;
  test(true, 2, true, true, true);
  test(true, 2, false, false, false);
  test(false, 2, true, true, true);
  test(false, 2, true, false, true);
  test(false, 2, false, true, false);
  test(false, 2, false, false, false);

  std::cout << "\n\n --- DYNAMIC TIMING SWITCH TESTS --- \n     Note that in the dual core tests, switching of timeEPglobal should not propagate to the MPFE servers, meaning that the switch has no effect. This is expected behavior.\n" << std::endl;
  test(true, 1, true, true, true, true);
  test(false, 1, false, false, false, true);
  test(false, 1, true, false, false, true);
  test(true, 1, true, false, false, true);
  test(true, 2, true, true, true, true);
  test(false, 2, false, false, false, true);
  test(false, 2, true, false, false, true);
  test(true, 2, true, false, false, true);

  std::cout << "\n\n ----- TEST II: USING ALL SUB-COMPONENTS SETTER ----- \n" << std::endl;

  std::cout << "\n\n --- SINGLE CORE TESTS --- \n" << std::endl;
  std::cout << "\n - single core: BEFORE -" << std::endl;
  test2(true, true, 1, true, true, true);
  test2(true, true, 1, false, false, false);
  test2(false, true, 1, true, true, true);
  test2(false, true, 1, true, false, true);
  test2(false, true, 1, false, true, false);
  test2(false, true, 1, false, false, false);
  std::cout << "\n - single core: AFTER -" << std::endl;
  test2(true,  false, 1, true, true, true);
  test2(true,  false, 1, false, false, false);
  test2(false, false, 1, true, true, true);
  test2(false, false, 1, true, false, true);
  test2(false, false, 1, false, true, false);
  test2(false, false, 1, false, false, false);

  std::cout << "\n\n --- DUAL CORE TESTS --- \n" << std::endl;
  std::cout << "\n - dual core: BEFORE -" << std::endl;
  test2(true,  true, 2, true, true, true);
  test2(true,  true, 2, false, false, false);
  test2(false, true, 2, true, true, true);
  test2(false, true, 2, true, false, true);
  test2(false, true, 2, false, true, false);
  test2(false, true, 2, false, false, false);

  std::cout << "\n - dual core: AFTER -" << std::endl;
  test2(true,  false, 2, true, true, true);
  test2(true,  false, 2, false, false, false);
  test2(false, false, 2, true, true, true);
  test2(false, false, 2, true, false, true);
  test2(false, false, 2, false, true, false);
  test2(false, false, 2, false, false, false);

  std::cout << "\n\n --- DYNAMIC TIMING SWITCH TESTS ---\n" << std::endl;
  std::cout << "\n - dynamic switch: BEFORE -" << std::endl;
  test2(true, true, 1, true, true, true, true);
  test2(false,true,  1, false, false, false, true);
  test2(false,true,  1, true, false, false, true);
  test2(true, true, 1, true, false, false, true);
  test2(true, true, 2, true, true, true, true);
  test2(false,true,  2, false, false, false, true);
  test2(false,true,  2, true, false, false, true);
  test2(true, true, 2, true, false, false, true);

  std::cout << "\n - dynamic switch: AFTER -" << std::endl;
  test2(true, false, 1, true, true, true, true);
  test2(false,false,  1, false, false, false, true);
  test2(false,false,  1, true, false, false, true);
  test2(true, false, 1, true, false, false, true);
  test2(true, false, 2, true, true, true, true);
  test2(false,false,  2, false, false, false, true);
  test2(false,false,  2, true, false, false, true);
  test2(true, false, 2, true, false, false, true);
}
