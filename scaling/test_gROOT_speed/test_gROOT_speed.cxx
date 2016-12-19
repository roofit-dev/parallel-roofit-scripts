#include <chrono>
#include <iostream>
#include <vector>

using namespace RooFit;

void test_gROOT_speed(int timing_flag = 3, int N_loops = 1000) {
  std::vector<float> timings(N_loops);

  RooConstVar roo_timing_flag("timing_flag", "timing_flag", timing_flag);
  gROOT->GetListOfSpecials()->Add(&roo_timing_flag);

  int count = 0;

  std::chrono::time_point<std::chrono::system_clock> begin, end;

  for (int i = 0; i < N_loops; ++i) {
    begin = std::chrono::high_resolution_clock::now();

    // count += static_cast<int>(dynamic_cast<RooConstVar*>(*gROOT->GetListOfSpecials()->begin())->getVal());
    count += static_cast<int>(static_cast<RooConstVar*>(*gROOT->GetListOfSpecials()->begin())->getVal());

    end = std::chrono::high_resolution_clock::now();

    float timing_s = std::chrono::duration_cast<std::chrono::nanoseconds>
                     (end-begin).count() / static_cast<float>(1e9);

    timings[i] = timing_s;
  }

  float mean, total, max, argmax;
  max = 0;

  for (int i = 0; i < N_loops; ++i) {
    total += timings[i];
    if (max < timings[i]) {
      max = timings[i];
      argmax = i;
    }
  }

  mean = total / N_loops;

  std::cout << "total: " << total << "s, mean: " << mean << "s" << std::endl;
  std::cout << "max: " << max << "s, argmax: " << argmax << std::endl;
}