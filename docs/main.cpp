#include "mic_cause_kernel.hpp"
#include <iostream>
int main(){
    using namespace mcik;
    Lattice1D<> lat(9, 1.0, 0.5);
    auto& g = lat.g(); g[4]=0.25;
    lat.forward(); lat.derive();
    auto col = lat.column(4);
    for(size_t i=0;i<col.size();++i) std::cout<<i<<\": \"<<col[i]<<\"\\n\";
    return 0;
}
