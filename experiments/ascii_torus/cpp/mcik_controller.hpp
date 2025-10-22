#pragma once
#include <algorithm>
#include <functional>
#include <utility>

namespace mcik_ctrl {

struct ParamVector {
  double resolution_scale;  // 0.25..1.0
  int    samples_per_pixel; // 1..4
  double gamma;             // 0.5..3.0 (render uses ~0.8..2.2)
  double normal_smooth;     // 0..1
  int    ramp_size;         // 8..16
};

struct StepSuggestion {
  ParamVector next;
  const char* mode; // "off" | "K" | "K+H"
};

inline ParamVector clamp_params(const ParamVector& p) {
  ParamVector q = p;
  q.resolution_scale = std::clamp(q.resolution_scale, 0.25, 1.0);
  q.samples_per_pixel = std::clamp(q.samples_per_pixel, 1, 4);
  q.gamma = std::clamp(q.gamma, 0.5, 3.0);
  q.normal_smooth = std::clamp(q.normal_smooth, 0.0, 1.0);
  q.ramp_size = std::clamp(q.ramp_size, 8, 16);
  return q;
}

struct ProbeDeltas {
  double d_scale = 0.05;
  int    d_spp = 1;
  double d_gamma = 0.1;
  double d_ns = 0.1;
  int    d_ramp = 2;
};

inline StepSuggestion suggest_step_K(const ParamVector& current,
                                     const std::function<double(const ParamVector&)>& evaluate,
                                     const ProbeDeltas& d = {}) {
  // Evaluate base
  const double base = evaluate(current);
  // Probe each parameter +/-
  struct Cand { ParamVector p; double score; const char* mode; } best{current, base, "K"};

  auto try_update = [&](ParamVector p){
    p = clamp_params(p);
    double s = evaluate(p);
    if (s > best.score) best = Cand{p, s, "K"};
  };

  // resolution_scale
  {
    ParamVector p = current; p.resolution_scale += d.d_scale; try_update(p);
    p = current; p.resolution_scale -= d.d_scale; try_update(p);
  }
  // samples_per_pixel
  {
    ParamVector p = current; p.samples_per_pixel += d.d_spp; try_update(p);
    p = current; p.samples_per_pixel -= d.d_spp; try_update(p);
  }
  // gamma
  {
    ParamVector p = current; p.gamma += d.d_gamma; try_update(p);
    p = current; p.gamma -= d.d_gamma; try_update(p);
  }
  // normal_smooth
  {
    ParamVector p = current; p.normal_smooth += d.d_ns; try_update(p);
    p = current; p.normal_smooth -= d.d_ns; try_update(p);
  }
  // ramp_size
  {
    ParamVector p = current; p.ramp_size += d.d_ramp; try_update(p);
    p = current; p.ramp_size -= d.d_ramp; try_update(p);
  }

  return StepSuggestion{best.p, best.mode};
}

inline StepSuggestion suggest_step_KH(const ParamVector& current,
                                      const std::function<double(const ParamVector&)>& evaluate,
                                      const ProbeDeltas& d = {}) {
  // First, best single from K
  StepSuggestion bestK = suggest_step_K(current, evaluate, d);
  double bestScore = evaluate(bestK.next);
  StepSuggestion best = bestK;

  // Consider selected pairs with simple two-point synergy measure
  auto try_pair = [&](auto apply_a, auto apply_b){
    ParamVector pa = clamp_params(apply_a(current));
    ParamVector pb = clamp_params(apply_b(current));
    ParamVector pab = clamp_params(apply_b(pa));
    double s0 = evaluate(current);
    double sa = evaluate(pa);
    double sb = evaluate(pb);
    double sab = evaluate(pab);
    double delta_a = sa - s0;
    double delta_b = sb - s0;
    double delta_ab = sab - s0;
    double synergy = delta_ab - (delta_a + delta_b);
    if (synergy > 0.0 && sab > bestScore) {
      bestScore = sab;
      best = StepSuggestion{pab, "K+H"};
    }
  };

  // Pair 1: resolution_scale × samples_per_pixel
  try_pair(
    [&](ParamVector p){ p.resolution_scale += d.d_scale; return p; },
    [&](ParamVector p){ p.samples_per_pixel += d.d_spp; return p; }
  );

  // Pair 2: gamma × normal_smooth
  try_pair(
    [&](ParamVector p){ p.gamma += d.d_gamma; return p; },
    [&](ParamVector p){ p.normal_smooth += d.d_ns; return p; }
  );

  // Pair 3: resolution_scale × gamma
  try_pair(
    [&](ParamVector p){ p.resolution_scale -= d.d_scale; return p; },
    [&](ParamVector p){ p.gamma += d.d_gamma; return p; }
  );

  return best;
}

inline StepSuggestion suggest_step(const ParamVector& current,
                                   const std::function<double(const ParamVector&)>& evaluate,
                                   bool useH) {
  return useH ? suggest_step_KH(current, evaluate) : suggest_step_K(current, evaluate);
}

} // namespace mcik_ctrl
