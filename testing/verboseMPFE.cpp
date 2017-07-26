/*
* @Author: E. G. Patrick Bos
* @Date:   2017-07-26 10:30:28
* @Last Modified by:   E. G. Patrick Bos
* @Last Modified time: 2017-07-26 13:42:19
*
* Run debug with root as executable, arguments:
*   -l -b verboseMPFE.cpp
* and working directory:
*   ~/projects/apcocsm/carsten
*/

using namespace RooFit;

void test() {
  TFile *_file0 = TFile::Open("simple/vbf.root");
  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
  RooAbsPdf* pdf = mc->GetPdf();
  RooAbsData * data = w->data("obsData");
  RooAbsReal* nll = pdf->createNLL(*data, RooFit::NumCPU(2, 0));

  RooAddition* ADDnll = dynamic_cast<RooAddition*>(nll);

  // actual nll
  RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(ADDnll->list().at(0));

  NLLnll->setVerboseMPFE();

  NLLnll->getValV();

  delete nll; // the dtor is virtual, so it will resolve to the correct dynamic type, RooAddition. delete ADDnll would work as well, but not both.
}

void test_smart() {
  TFile *_file0 = TFile::Open("simple/vbf.root");
  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
  RooAbsPdf* pdf = mc->GetPdf();
  RooAbsData * data = w->data("obsData");
  RooAbsReal * nll = pdf->createNLL(*data, RooFit::NumCPU(2, 0));
  
  std::unique_ptr<RooAddition> ADDnll(dynamic_cast<RooAddition*>(nll));

  // actual nll
  RooNLLVar * NLLnll = dynamic_cast<RooNLLVar *>(ADDnll->list().at(0));

  NLLnll->setVerboseMPFE();

  NLLnll->getValV();
}

void verboseMPFE() {
  // remove INFO stream to keep output clean
  RooMsgService::instance().deleteStream(1);
  // add relevant DEBUG streams
  RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::ClassName("RooRealMPFE")); // RooFit::Topic(RooFit::Optimization)

  std::cout << "\n\n --- RAW POINTER TEST--- \n" << std::endl;
  test();
  std::cout << "\n\n --- SMART POINTER TEST--- \n" << std::endl;
  test_smart();
}