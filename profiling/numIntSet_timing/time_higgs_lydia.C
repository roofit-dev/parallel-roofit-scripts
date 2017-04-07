// run in subdir as
// root -b -q -l ../../../../lydia/workspace-run2-ggf.root '../time_higgs_lydia.C(1,1)'

using namespace RooFit;

// only used for dataset Lydia 2:
using namespace RooStats;
using namespace HistFactory;

const char* project_dir = "/Users/pbos/projects/apcocsm";
const char* run_subdir = "code/profiling/numIntSet_timing/run_time_higgs_lydia1";

void time_higgs_lydia(int dataset, int num_cpu, int debug=0, int parallel_interleave=0,
                       int seed=1, int print_level=0) 
{  
  gSystem->ChangeDirectory(project_dir);

  TFile *_file0;
  const char* workspace_name;
  const char* obsdata_name;
  bool set_muGGF;
  bool perturb_parameters_randomly;

  // load dataset file and settings
  switch (dataset) {
    case 1: {
      _file0 = TFile::Open("lydia/workspace-run2-ggf.root");
      workspace_name = "Run2GGF";
      obsdata_name = "asimovData";
      set_muGGF = true;
      perturb_parameters_randomly = true;
      break;
    }

    case 2: {
      std::cout << "WARNING: this dataset only works with HiggsComb ROOT (on stoomboot: lsetup \"root 5.34.32-HiggsComb-x86_64-slc6-gcc48-opt\")" << std::endl;
      _file0 = TFile::Open("lydia/9channel_20150304_incl_tH_couplings_7TeV_8TeV_test_full_fixed_theory_asimov_7TeV_8TeV_THDMII.root");
      workspace_name = "combined";
      obsdata_name = "combData";
      set_muGGF = false;
      perturb_parameters_randomly = false;
      break;
    }
  }
  
  gSystem->ChangeDirectory(run_subdir);

  gRandom->SetSeed(seed);

  // activate debugging output
  if (debug == 1) {
    RooMsgService::instance().addStream(DEBUG);  // all DEBUG messages
    // RooMsgService::instance().addStream(DEBUG, Topic(RooFit::Eval), ClassName("RooAbsTestStatistic"));
  }

  // TStopwatch t;
  // t.Start();

  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get(workspace_name));
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

  if (set_muGGF) {
    w->var("muGGF")->setVal(3);
  }
  //w->loadSnapshot("NominalParamValues");

  RooAbsData* obsData = w->data(obsdata_name);
  RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName());

  if (perturb_parameters_randomly) {
    // NOT REALLY NECESSARY FOR TESTING, IT MAKES THE FIT A BIT HARDER
    RooArgSet* params = static_cast<RooArgSet*>(pdf->getParameters(obsData)->selectByAttrib("Constant",kFALSE));
    RooFIter iter = params->fwdIterator();
    RooAbsRealLValue* arg;
    while ((arg=(RooAbsRealLValue*)iter.next())) {
      arg->setVal(arg->getVal()+gRandom->Gaus(0,0.3));
    }
  }

  // activate debugging output
  if (debug == 2) {
    RooMsgService::instance().addStream(DEBUG);  // all DEBUG messages
    // RooMsgService::instance().addStream(DEBUG, Topic(RooFit::Eval), ClassName("RooAbsTestStatistic"));
  }

  RooMsgService::instance().addStream(DEBUG, Topic(RooFit::Generation), ClassName("RooRealMPFE"));

  RooAbsReal* nll = pdf->createNLL(*obsData,
                                   Constrain(*w->set("ModelConfig_NuisParams")),
                                   GlobalObservables(*w->set("ModelConfig_GlobalObservables")),
                                   Offset(kTRUE),
                                   NumCPU(num_cpu, parallel_interleave)
                                   );

  RooMinimizer m(*nll);
  m.setVerbose(print_level);
  m.setStrategy(0);  // this sets the minuit strategy to optimal for "fast functions" (2 is for slow, 1 for intermediate)
  // m.setProfile(1);  // this is for activating profiling of the minimizer
  m.optimizeConst(2);

  std::cout << "\n\n\n\nSTART MINIMIZE\n\n\n\n" << std::endl;
  
  m.minimize("Minuit2","migrad");

}
