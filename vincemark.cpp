// call from command line like, for instance:
// root -l 'vincemark.cpp()'

#include <chrono>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <unistd.h>  // usleep
#include <sys/types.h>  // for kill
#include <signal.h>     // for kill

using namespace RooFit;

std::string cut_between(std::string input, std::string before, std::string after) {
  auto before_pos = input.find(before);
  auto after_pos = input.find(after);
  auto cut_pos = before_pos + before.length();
  auto cut_len = after_pos - cut_pos;
  std::string output = input.substr(cut_pos, cut_len);
  return output;
}


////////////////////////////////////////////////////////////////////////////////////////////////////
// timing_flag is used to activate only selected timing statements [1-7]
// num_cpu: -1 is special option -> compare overhead communication protocol (wrt 1 cpu)
// parallel_interleave: 0 = blocks of equal size, 1 = interleave
////////////////////////////////////////////////////////////////////////////////////////////////////

void vincemark(std::string workspace_filepath,
               int num_cpu=1,
               int optConst=0,
               int parallel_interleave=0,
               bool cpu_affinity=true,
               int seed=1,
               int timing_flag=1,
               bool time_num_ints=false,
               bool fork_timer = false,
               int fork_timer_sleep_us = 100000,
               int print_level=0,
               bool debug=false
               ) {
  if (debug) {
    RooMsgService::instance().addStream(DEBUG);
    // extra possible options: Topic(Generation) Topic(RooFit::Eval), ClassName("RooAbsTestStatistic")
  }

  // int N_parameters(8);  // must be even, means and sigmas have diff ranges

  if (timing_flag > 0) {
    RooJsonListFile outfile;
  
    outfile.open("timing_meta.json");
    std::string names[13] = {"workspace_filepath",
                             "N_chans", "N_bins", "N_nuisance_parameters",
                             "N_events", "num_cpu", "parallel_interleave",
                             "seed", "pid", "time_num_ints",
                             "optConst", "print_level", "timing_flag"};
    outfile.set_member_names(names, names + 13);

    auto workspace_fn = workspace_filepath.substr(workspace_filepath.rfind("/"));

    std::string N_channels = cut_between(workspace_fn, "workspace", "channels");
    std::string N_events = cut_between(workspace_fn, "channels", "events");
    std::string N_bins = cut_between(workspace_fn, "events", "bins");
    std::string N_nuisance_parameters = cut_between(workspace_fn, "bins", "nps");

    outfile << workspace_filepath << N_channels << N_bins << N_nuisance_parameters
            << N_events << num_cpu << parallel_interleave
            << seed << getpid() << time_num_ints
            << optConst << print_level << timing_flag;
  }

  RooTrace::timing_flag = timing_flag;
  if (time_num_ints) {
    RooTrace::set_time_numInts(kTRUE);
  }

  // plotting configuration
  int obs_plot_x(3);
  int obs_plot_y(2);
  int obs_plot_x_px(1200);
  int obs_plot_y_px(800);

  // other stuff
  int printlevel(print_level);
  int optimizeConst(optConst);
  // int N_timing_loops(3); // not used

  gRandom->SetSeed(seed);

  // Load the workspace data and pdf
  TFile *_file0 = TFile::Open(workspace_filepath.c_str());
  
  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("BinnedWorkspace"));
  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));

  RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName()) ;
  RooAbsData * data = w->data("obsData");


  // --- Perform extended ML fit of composite PDF to data ---

  RooJsonListFile outfile;
  RooWallTimer timer;
  
  if (timing_flag == 1) {
    outfile.open("timing_full_minimize.json");
    outfile.add_member_name("walltime_s")
           .add_member_name("segment")
           .add_member_name("pid");
  }

  Bool_t cpuAffinity;
  if (cpu_affinity) {
    cpuAffinity = kTRUE;
  } else {
    cpuAffinity = kFALSE;
  }

  // for (int it = 0; it < N_timing_loops; ++it)
  {
    RooAbsReal* nll = pdf->createNLL(*data, NumCPU(num_cpu, parallel_interleave),
                                     CPUAffinity(cpuAffinity));//, "Extended");
    RooMinimizer m(*nll);
    // m.setVerbose(1);
    m.setStrategy(0);
    m.setProfile(1);
    m.setPrintLevel(printlevel);
    m.optimizeConst(optimizeConst);

    int pid = -1;

    if (fork_timer) {
      pid = fork();
    }
    if (pid == 0) {
      /* child */
      timer.start();
      while (true) {
        timer.stop();
        std::cout << "TIME: " << timer.timing_s() << "s" << std::endl;
        usleep(fork_timer_sleep_us);
      }
    }
    else {
      /* parent */

      double time_migrad, time_hesse, time_minos;

      if (timing_flag == 1) {
        timer.start();
      }
      // m.hesse();

      m.migrad();

      if (timing_flag == 1) {
        timer.stop();
        std::cout << "TIME migrad: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "migrad" << getpid();
        time_migrad = timer.timing_s();

        timer.start();
      }

      m.hesse();

      if (timing_flag == 1) {
        timer.stop();
        std::cout << "TIME hesse: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "hesse" << getpid();
        time_hesse = timer.timing_s();

        timer.start();
      }

      m.minos(*mc->GetParametersOfInterest());

      if (timing_flag == 1) {
        timer.stop();
        std::cout << "TIME minos: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "minos" << getpid();
        time_minos = timer.timing_s();

        outfile << (time_migrad + time_hesse + time_minos) << "migrad+hesse+minos" << getpid();
      }

      if (pid > 0) {
        // a child exists
        kill(pid, SIGKILL);
      }
    }
  }
}
