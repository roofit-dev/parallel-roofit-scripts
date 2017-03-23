// run in subdir as
// root -b -q -l ../../../../lydia/workspace-run2-ggf.root '../time_higgs_lydia1.C(1)'

using namespace RooFit;

void time_higgs_lydia1(int num_cpu, int parallel_interleave=0,
                       int seed=1, int print_level=0) 
{  
  gRandom->SetSeed(seed);

  // TStopwatch t;
  // t.Start();

  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("Run2GGF"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));

  // Activate binned likelihood calculation for binned models
  if (1) {
    RooFIter iter = w->components().fwdIterator();
    RooAbsArg* arg;
    while((arg=iter.next())) {
      if (arg->IsA()==RooRealSumPdf::Class()) {
        arg->setAttribute("BinnedLikelihood");
        cout << "component " << arg->GetName() << " is a binned likelihood" << endl;
      }
      if (arg->IsA()==RooAddPdf::Class() && TString(arg->GetName()).BeginsWith("pdf_")) {
        arg->setAttribute("MAIN_MEASUREMENT");
        cout << "component " << arg->GetName() << " is a cms main measurement" << endl;
      }
    }
  }

  w->var("muGGF")->setVal(3);
  //w->loadSnapshot("NominalParamValues");

  //RooAbsData* obsData = w->data("combData");
  RooAbsData* obsData = w->data("asimovData");
  RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName());

  //
  //
  // THIS PART NOT REALLY NECESSARY FOR TESTING, IT MAKES THE FIT A BIT HARDER
  //
  RooArgSet* params = static_cast<RooArgSet*>(pdf->getParameters(obsData)->selectByAttrib("Constant",kFALSE));
  RooFIter iter = params->fwdIterator();
  RooAbsRealLValue* arg;
  while ((arg=(RooAbsRealLValue*)iter.next())) {
    arg->setVal(arg->getVal()+gRandom->Gaus(0,0.3));
  }
  //
  // ABOVE PART NOT REALLY NECESSARY FOR TESTING, IT MAKES THE FIT A BIT HARDER
  //
  //

  RooAbsReal* nll = pdf->createNLL(*obsData,
                                   Constrain(*w->set("ModelConfig_NuisParams")),
                                   GlobalObservables(*w->set("ModelConfig_GlobalObservables")),
                                   Offset(kTRUE),
                                   NumCPU(num_cpu, parallel_interleave)
                                   );

  RooMinimizer m(*nll);
  m.setVerbose(print_level);
  std::cout << "\n\n\n\nHERE? 1\n\n\n\n" << std::endl;
  m.setStrategy(0);
  std::cout << "\n\n\n\nHERE? 2\n\n\n\n" << std::endl;
  m.setProfile(1);
  std::cout << "\n\n\n\nHERE? 3\n\n\n\n" << std::endl;
  m.optimizeConst(2);
  std::cout << "\n\n\n\nHERE? 4\n\n\n\n" << std::endl;
  
  m.minimize("Minuit2","migrad");

}
