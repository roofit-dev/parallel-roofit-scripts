// run as
// root -l -b -q  model_to_graphviz.C

using namespace RooFit ;


void model_to_graphviz()
{

  // Lydia 1

  // TFile *_file0 = TFile::Open("/user/pbos/lydia/workspace-run2-ggf.root");
  TFile *_file0 = TFile::Open("/user/pbos/lydia/lydia1.root");

  RooWorkspace* w1 = static_cast<RooWorkspace*>(gDirectory->Get("Run2GGF"));
  RooStats::ModelConfig* mc1 = static_cast<RooStats::ModelConfig*>(w1->genobj("ModelConfig"));
  RooAbsPdf* pdf1 = w1->pdf(mc1->GetPdf()->GetName()) ;
  // pdf1->Print() ;

  pdf1->graphVizTree("/user/pbos/lydia/lydia1.dot") ;

  // Lydia 2

  // TFile *_file2 = TFile::Open("/user/pbos/lydia/9channel_20150304_incl_tH_couplings_7TeV_8TeV_test_full_fixed_theory_asimov_7TeV_8TeV_THDMII.root");
  TFile *_file2 = TFile::Open("/user/pbos/lydia/lydia2.root");

  RooWorkspace* w2 = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
  RooStats::ModelConfig* mc2 = static_cast<RooStats::ModelConfig*>(w2->genobj("ModelConfig"));
  RooAbsPdf* pdf2 = w2->pdf(mc2->GetPdf()->GetName()) ;

  pdf2->graphVizTree("/user/pbos/lydia/lydia2.dot") ;

}
