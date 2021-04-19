// call from command line like, for instance:
// root -l 'higgs_fit_20210310.cpp(...)'

R__LOAD_LIBRARY(libRooFit)

#include <chrono>
#include <iostream>
#include <fstream>
#include <sstream>

using namespace RooFit;

////////////////////////////////////////////////////////////////////////////////////////////////////
// timing_flag is used to activate only selected timing statements [1-7]
// num_cpu: -1 is special option -> compare overhead communication protocol (wrt 1 cpu)
// parallel_interleave: 0 = blocks of equal size, 1 = interleave, 2 = simultaneous pdfs mode
//                      { BulkPartition=0, Interleave=1, SimComponents=2, Hybrid=3 }
////////////////////////////////////////////////////////////////////////////////////////////////////

std::tuple<std::string, std::string, std::string, std::string, std::size_t> read_config_file(const char * config_filename) {
  std::string workspace_filename, workspace_name, dataset_name, modelconfig_name, NumCPU_s;
  std::size_t NumCPU;

  std::ifstream workspace_file_config_file(config_filename);
  if (workspace_file_config_file.is_open()) {
    std::getline(workspace_file_config_file, workspace_filename);
    std::getline(workspace_file_config_file, workspace_name);
    std::getline(workspace_file_config_file, dataset_name);
    std::getline(workspace_file_config_file, modelconfig_name);
    std::getline(workspace_file_config_file, NumCPU_s);
    std::stringstream ss;
    ss << NumCPU_s;
    ss >> NumCPU;
  } else {
    throw std::runtime_error("Could not open workspace_benchmark.conf configuration file");
  }
  return {workspace_filename, workspace_name, dataset_name, modelconfig_name, NumCPU};
}

void higgs_fit_20210310(const char* config_filename, bool use_multiprocess = true) {
    RooMsgService::instance().deleteStream(0);
    RooMsgService::instance().deleteStream(0);

    RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Benchmarking1));
    RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Benchmarking2));

    std::size_t seed = 1;
    RooRandom::randomGenerator()->SetSeed(seed);

    // read filename and dataset / modelconfig names from configuration file
    std::string workspace_filename, workspace_name, dataset_name, modelconfig_name;
    std::size_t NumCPU;
    std::tie(workspace_filename, workspace_name, dataset_name, modelconfig_name, NumCPU) = read_config_file(config_filename);

    TFile *_file0 = TFile::Open(workspace_filename.c_str());

    RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get(workspace_name.c_str()));

    RooAbsData *data = w->data(dataset_name.c_str());
    auto mc = dynamic_cast<RooStats::ModelConfig *>(w->genobj(modelconfig_name.c_str()));
    auto global_observables = mc->GetGlobalObservables();
    auto nuisance_parameters = mc->GetNuisanceParameters();
    RooAbsPdf *pdf = w->pdf(mc->GetPdf()->GetName());

    std::unique_ptr<RooMinimizer> m;

    // w->var("mu")->setVal(1.5);

    if (use_multiprocess) {
        RooFit::MultiProcess::JobManager::default_N_workers = NumCPU;
        auto likelihood = RooFit::TestStatistics::build_simultaneous_likelihood(pdf, data, RooFit::TestStatistics::ConstrainedParameters(*nuisance_parameters), RooFit::TestStatistics::GlobalObservables(*global_observables));
        m = RooMinimizer::create<RooFit::TestStatistics::LikelihoodSerial, RooFit::TestStatistics::LikelihoodGradientJob>(likelihood);
        m->enable_likelihood_offsetting(true);
    } else {
        RooAbsReal *nll = pdf->createNLL(*data,
                                         RooFit::GlobalObservables(*global_observables),
                                         RooFit::Constrain(*nuisance_parameters),
                                         RooFit::Offset(kTRUE));

        m = RooMinimizer::create(*nll);
    }

    m->setPrintLevel(1);
    m->setStrategy(0);
    m->setProfile(false);
    m->optimizeConst(2);
    m->setMinimizerType("Minuit2");
    // m->setVerbose(kTRUE);

    auto get_time = [](){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();};

    auto start = std::chrono::high_resolution_clock::now();
    std::cout << "start migrad at " << get_time() << std::endl;
    m->migrad();
    std::cout << "end migrad at " << get_time() << std::endl;
    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed_seconds =
        std::chrono::duration_cast<std::chrono::duration<double>>(
            end - start).count();
    std::cout << "migrad: " << elapsed_seconds << "s" << std::endl;

    m->cleanup();
}
