#include <ctime>
#include <iostream>

int main() {
  clock_t begin = clock();

  double a(1.01);

  for (int i = 0; i < 100000; ++i) {
    a += a;
  }

  clock_t end = clock();

  std::cout << "a: " << a << std::endl;

  double c_timing_s = (end - begin) / static_cast<double>(CLOCKS_PER_SEC);
  double c_timing_s_2 = static_cast<double>(end - begin) / static_cast<double>(CLOCKS_PER_SEC);

  std::cout << "begin:        " << begin << std::endl;
  std::cout << "end:          " << end << std::endl;
  std::cout << "c_timing_s:   " << c_timing_s << std::endl;
  std::cout << "c_timing_s_2: " << c_timing_s_2 << std::endl;
}