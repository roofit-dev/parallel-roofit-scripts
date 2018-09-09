// WorkBench: benchmark workspaces by optimizing the PDF parameters wrt the data
//
// call from command line like, for instance:
// root -l 'workbench.cpp()'

R__LOAD_LIBRARY(libRooFit)

#include <chrono>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <list>
#include <unistd.h>  // usleep
#include <sys/types.h>  // for kill
#include <signal.h>     // for kill
#include <ctime>

using namespace RooFit;

////////////////////////////////////////////////////////////////////////////////////////////////////
// timing_flag is used to activate only selected timing statements [1-7]
// num_cpu: -1 is special option -> compare overhead communication protocol (wrt 1 cpu)
// parallel_interleave: 0 = blocks of equal size, 1 = interleave, 2 = simultaneous pdfs mode
//                      { BulkPartition=0, Interleave=1, SimComponents=2, Hybrid=3 }
////////////////////////////////////////////////////////////////////////////////////////////////////

void workbench_sarajevo(std::string workspace_filepath,
               int num_cpu=1,
               std::string workspace_name="HWWRun2GGF",
               std::string model_config_name="ModelConfig",
               std::string data_name="obsData",
               int optConst=2,
               int parallel_interleave=0,
               bool cpu_affinity=true,
               int seed=1,
               int timing_flag=1,
               bool time_num_ints=false,
               bool fork_timer = false,
               int fork_timer_sleep_us = 100000,
               int print_level=0,
               bool debug=false,
               bool total_cpu_timing=true,
               bool fix_binned_pdfs=false,
               bool zero_initial_POI=false,
               std::string POI_name=""
               // bool callNLLfirst=false
               ) {
  if (debug) {
    RooMsgService::instance().addStream(DEBUG);
    // extra possible options: Topic(Generation) Topic(RooFit::Eval), ClassName("RooAbsTestStatistic")
  }

  // int N_parameters(8);  // must be even, means and sigmas have diff ranges

  if (timing_flag > 0) {
    RooJsonListFile outfile;
  
    outfile.open("timing_meta.json");
    std::list<std::string> names = {"timestamp",
                                    "workspace_filepath", "workspace_name",
                                    "model_config_name", "data_name",
                                    "num_cpu", "parallel_interleave", "cpu_affinity",
                                    "seed", "pid", "time_num_ints",
                                    "optConst", "print_level", "timing_flag"};
    outfile.set_member_names(names.begin(), names.end());

    // int timestamp = std::time(nullptr);

    outfile << std::time(nullptr)
            << workspace_filepath << workspace_name
            << model_config_name << data_name
            << num_cpu << parallel_interleave << cpu_affinity
            << seed << getpid() << time_num_ints
            << optConst << print_level << timing_flag;
  }

  RooTrace::timing_flag = timing_flag;
  if (time_num_ints) {
    RooTrace::set_time_numInts(kTRUE);
  }

  // other stuff
  int printlevel(print_level);
  int optimizeConst(optConst);
  // int N_timing_loops(3); // not used

  if (printlevel == 0) {
    RooMsgService::instance().setGlobalKillBelow(RooFit::ERROR);
  }

  RooRandom::randomGenerator()->SetSeed(seed);

  // Load the workspace data and pdf
  TFile *_file0 = TFile::Open(workspace_filepath.c_str());
  
  RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get(workspace_name.c_str()));

  // Activate binned likelihood calculation for binned models
  if (fix_binned_pdfs) {
    RooFIter iter = w->components().fwdIterator();
    RooAbsArg* component_arg;
    while((component_arg = iter.next())) {
      if (component_arg->IsA() == RooRealSumPdf::Class()) {
        component_arg->setAttribute("BinnedLikelihood");
        std::cout << "component " << component_arg->GetName() << " is a binned likelihood" << std::endl;
      }
    }
  }

  RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj(model_config_name.c_str()));

  // RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName()) ;
  RooAbsPdf* pdf = mc->GetPdf();
  RooAbsData * data = w->data(data_name.c_str());


  // Manually set initial values of parameter of interest
  if (zero_initial_POI) {
    if (POI_name.length() > 0) {
      RooAbsRealLValue* POI = static_cast<RooAbsRealLValue *>(pdf->getParameters(data)->selectByName(POI_name.c_str())->first());
      POI->setVal(0);
    } else {
      std::cout << "POI_name is empty!" << std::endl;
      exit(1);
    }
  }


  // --- Perform extended ML fit of composite PDF to data ---

  RooJsonListFile outfile;
  RooWallTimer timer;
  
  if (timing_flag == 1) {
    outfile.open("timing_full_minimize.json");
    outfile.add_member_name("walltime_s")
           .add_member_name("segment")
           .add_member_name("pid");
  }

  RooJsonListFile outfile_cpu;
  RooCPUTimer ctimer;
  
  if (total_cpu_timing) {
    outfile_cpu.open("timing_full_minimize_cpu.json");
    outfile_cpu.add_member_name("cputime_s")
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
    RooAbsReal* RARnll(pdf->createNLL(*data, NumCPU(num_cpu, parallel_interleave),
                       CPUAffinity(cpuAffinity)));//, "Extended");
    // std::shared_ptr<RooAbsTestStatistic> nll(dynamic_cast<RooAbsTestStatistic*>(RARnll)); // shared_ptr gives odd error in ROOT cling!
    // RooAbsTestStatistic * nll = dynamic_cast<RooAbsTestStatistic*>(RARnll);

    // if (time_evaluate_partition) {
    //   nll->setTimeEvaluatePartition(kTRUE);
    // }

    // if (callNLLfirst) {
    //   RARnll->getVal();
    // }

    RooMinimizer m(*RARnll);
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
      double ctime_migrad, ctime_hesse, ctime_minos;

      if (timing_flag == 1) {
        timer.start();
      }
      if (total_cpu_timing) {
        ctimer.start();
      }
      // m.hesse();

      m.migrad();

      if (timing_flag == 1) {
        timer.stop();
      }
      if (total_cpu_timing) {
        ctimer.stop();
      }
      if (timing_flag == 1) {
        std::cout << "TIME migrad: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "migrad" << getpid();
        time_migrad = timer.timing_s();
      }
      if (total_cpu_timing) {
        std::cout << "CPUTIME migrad: " << ctimer.timing_s() << "s" << std::endl;
        outfile_cpu << ctimer.timing_s() << "migrad" << getpid();
        ctime_migrad = ctimer.timing_s();
      }
      if (timing_flag == 1) {
        timer.start();
      }
      if (total_cpu_timing) {
        ctimer.start();
      }

      m.hesse();

      if (timing_flag == 1) {
        timer.stop();
      }
      if (total_cpu_timing) {
        ctimer.stop();
      }
      if (timing_flag == 1) {
        std::cout << "TIME hesse: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "hesse" << getpid();
        time_hesse = timer.timing_s();
      }
      if (total_cpu_timing) {
        std::cout << "CPUTIME hesse: " << ctimer.timing_s() << "s" << std::endl;
        outfile_cpu << ctimer.timing_s() << "hesse" << getpid();
        ctime_hesse = ctimer.timing_s();
      }
      if (timing_flag == 1) {
        timer.start();
      }
      if (total_cpu_timing) {
        ctimer.start();
      }


      m.minos(*mc->GetParametersOfInterest());

      if (timing_flag == 1) {
        timer.stop();
      }
      if (total_cpu_timing) {
        ctimer.stop();
      }
      if (timing_flag == 1) {
        std::cout << "TIME minos: " << timer.timing_s() << "s" << std::endl;
        outfile << timer.timing_s() << "minos" << getpid();
        time_minos = timer.timing_s();

        outfile << (time_migrad + time_hesse + time_minos) << "migrad+hesse+minos" << getpid();
      }
      if (total_cpu_timing) {
        std::cout << "CPUTIME minos: " << ctimer.timing_s() << "s" << std::endl;
        outfile_cpu << ctimer.timing_s() << "minos" << getpid();
        ctime_minos = ctimer.timing_s();

        outfile_cpu << (ctime_migrad + ctime_hesse + ctime_minos) << "migrad+hesse+minos" << getpid();
      }

      if (pid > 0) {
        // a child exists
        kill(pid, SIGKILL);
      }
    }

    delete RARnll;
  }
}
