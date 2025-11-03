#include "mcik/mic_cause_kernel.hpp"

#include <cstddef>
#include <iostream>

int main() {
  mcik::Lattice1D<> lattice(9, 1.0, 0.5);
  auto& state = lattice.g();
  state[4] = 0.25;

  lattice.forward();
  lattice.derive();

  auto column = lattice.column(4);
  for (std::size_t i = 0; i < column.size(); ++i) {
    std::cout << i << ": " << column[i] << "\n";
  }

  return 0;
}
