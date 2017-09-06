#ifndef __CINT__
#include "RooGlobalFunc.h"
#endif

R__LOAD_LIBRARY(libRooFit)
#include "TFile.h"
#include "TROOT.h"
#include "RooWorkspace.h"
#include "TFile.h"
#include "TH1.h"


using namespace RooFit;

void runBinnedTest() 
{
  TFile *infile = TFile::Open("workspace.root");
  RooWorkspace *w = static_cast<RooWorkspace*>(infile->Get("BinnedWorkspace"));
  RooAbsData *data = w->data("obsData");
  RooStats::ModelConfig *mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
  RooAbsPdf *pdf = w->pdf(mc->GetPdf()->GetName());
  RooAbsReal *nll = pdf->createNLL(*data, NumCPU(2,0));
  RooMinimizer m(*nll);
  m.setStrategy(0);
  m.setProfile(1);
  m.migrad();
  m.hesse();
  m.minos();
  delete nll;
}
