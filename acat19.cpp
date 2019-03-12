// call from command line like, for instance:
// root -l 'acat19.cpp()'

R__LOAD_LIBRARY(libRooFit)

#include <chrono>
#include <iostream>

using namespace RooFit;

////////////////////////////////////////////////////////////////////////////////////////////////////
// timing_flag is used to activate only selected timing statements [1-7]
// num_cpu: -1 is special option -> compare overhead communication protocol (wrt 1 cpu)
// parallel_interleave: 0 = blocks of equal size, 1 = interleave, 2 = simultaneous pdfs mode
//                      { BulkPartition=0, Interleave=1, SimComponents=2, Hybrid=3 }
////////////////////////////////////////////////////////////////////////////////////////////////////

void acat19() {
    TFile *_file0 = TFile::Open("/user/pbos/data_atlas/carsten/comb-5xs-80ifb-v8.root");

    RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combWS"));

    RooAbsData *data = w->data("combData");
    auto mc = dynamic_cast<RooStats::ModelConfig *>(w->genobj("ModelConfig"));
    auto global_observables = mc->GetGlobalObservables();
    auto nuisance_parameters = mc->GetNuisanceParameters();
    RooAbsPdf *pdf = w->pdf(mc->GetPdf()->GetName());

    w->var("mu")->setVal(1.5);

    RooAbsReal *nll = pdf->createNLL(*data,
                            RooFit::GlobalObservables(*global_observables),
                            RooFit::Constrain(*nuisance_parameters),
                            RooFit::Offset(kTRUE));

    RooFit::MultiProcess::GradMinimizer m(*nll, 1);

    m.setPrintLevel(-1);
    m.setStrategy(0);
    m.setProfile(false);
    m.optimizeConst(2);
    m.setMinimizerType("Minuit2");
    m.setVerbose(kTRUE);

    auto start = std::chrono::high_resolution_clock::now();
    m.migrad();
    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed_seconds =
        std::chrono::duration_cast<std::chrono::duration<double>>(
            end - start).count();
    std::cout << "migrad: " << elapsed_seconds << "s" << std::endl;
}
