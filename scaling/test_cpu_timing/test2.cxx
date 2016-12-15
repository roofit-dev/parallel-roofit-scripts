#include <ctime>
#include <iostream>

int main() {
  struct timespec begin, end;
  clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &begin);

  double a(1.01);

  for (int i = 0; i < 100000; ++i) {
    a += a;
  }

  clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &end);

  std::cout << "a: " << a << std::endl;

  double c_timing_ns = (end.tv_nsec - begin.tv_nsec);

  std::cout << "begin:         " << begin.tv_nsec << std::endl;
  std::cout << "end:           " << end.tv_nsec << std::endl;
  std::cout << "c_timing_ns:   " << c_timing_ns << std::endl;
  std::cout << "c_timing_ns_2: " << c_timing_ns_2 << std::endl;

  clock_getres(CLOCK_PROCESS_CPUTIME_ID, &end);
  std::cout << "resolution ns: " << end.tv_nsec << std::endl;
}