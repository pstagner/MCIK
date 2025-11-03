#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <iomanip>
#include <climits>
#include <fstream>
#include <sstream>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include "mcik/experiments/ascii_torus/metrics.hpp"
#include "mcik/experiments/ascii_torus/controller.hpp"

// Simple ASCII torus renderer with optional controller (K or K+H)
// - stdout interactive loop with ANSI clear/home
// - HUD shows FPS, target, params, controller mode
// - CSV logging in batch mode
// - Hotkeys (interactive): 1=off, 2=K, 3=K+H, +=FPS up, -=FPS down, q=quit
// - Quality uses edge gradient and similarity vs a high-quality reference frame
//
// CLI flags:
//   --resolution-scale <float>
//   --samples-per-pixel <int>
//   --gamma <float>
//   --normal-smooth <float>
//   --ramp-size <int>
//   --target-fps <int>
//   --mode <interactive|batch|synergy|benchmark>
//   --frames <int> (batch/benchmark)
//   --controller <off|K|KH>
//   --ctrl-interval <int> (frames)
//   --w-fps <float>
//   --w-quality <float>
//   --torus-R <float>
//   --torus-r <float>
//   --cam-dist <float>
//   --log-csv <path> (batch/benchmark)

struct RenderParams {
  int base_width = 80;
  int base_height = 24;
  double resolution_scale = 1.0;      // 0.25..1.0
  int samples_per_pixel = 1;          // 1..4 (not used in baseline)
  double gamma = 1.0;                 // 0.8..2.2
  double normal_smooth = 0.0;         // 0..1 (not used in baseline)
  int ramp_size = 12;                 // 8..16
  int target_fps = 30;
  std::string mode = "interactive";   // or "batch" or "synergy" or "benchmark"
  int frames = 300;                   // for batch/benchmark
  std::string controller = "off";     // off|K|KH
  int ctrl_interval = 10;             // evaluate controller every N frames
  double w_fps = 0.5;
  double w_quality = 0.5;
  double torus_R = 2.5;
  double torus_r = 0.30;
  double cam_distance = 10.0;
  std::string log_csv;                // batch/benchmark logging path
};

static const char* DEFAULT_RAMP = " .:-=+*#%@adkfkajnondvakdfaoivqevlasdkjfacvu"; // length 10

struct FrameStats {
  double fps = 0.0;
  double ms = 0.0;
};

struct TorusModel {
  // Torus radii (major R, minor r)
  double R = 2.5;  // distance from center of tube to center of torus
  double r = 0.30;  // tube radius
};

struct Camera {
  double distance = 10.0; // distance from origin along +z (after rotation)
};

static void parse_args(int argc, char** argv, RenderParams& params) {
  for (int i = 1; i < argc; ++i) {
    std::string a = argv[i];
    auto next = [&](double& out){ if (i + 1 < argc) out = std::stod(argv[++i]); };
    auto nexti = [&](int& out){ if (i + 1 < argc) out = std::stoi(argv[++i]); };
    auto nexts = [&](std::string& out){ if (i + 1 < argc) out = argv[++i]; };
    if (a == "--resolution-scale") next(params.resolution_scale);
    else if (a == "--samples-per-pixel") nexti(params.samples_per_pixel);
    else if (a == "--gamma") next(params.gamma);
    else if (a == "--normal-smooth") next(params.normal_smooth);
    else if (a == "--ramp-size") nexti(params.ramp_size);
    else if (a == "--target-fps") nexti(params.target_fps);
    else if (a == "--mode") nexts(params.mode);
    else if (a == "--frames") nexti(params.frames);
    else if (a == "--controller") nexts(params.controller);
    else if (a == "--ctrl-interval") nexti(params.ctrl_interval);
    else if (a == "--w-fps") next(params.w_fps);
    else if (a == "--w-quality") next(params.w_quality);
    else if (a == "--torus-R") next(params.torus_R);
    else if (a == "--torus-r") next(params.torus_r);
    else if (a == "--cam-dist") next(params.cam_distance);
    else if (a == "--log-csv") nexts(params.log_csv);
  }
  params.resolution_scale = std::clamp(params.resolution_scale, 0.25, 1.0);
  params.samples_per_pixel = std::clamp(params.samples_per_pixel, 1, 4);
  params.gamma = std::clamp(params.gamma, 0.5, 3.0);
  params.normal_smooth = std::clamp(params.normal_smooth, 0.0, 1.0);
  params.ramp_size = std::clamp(params.ramp_size, 8, 16);
  params.target_fps = std::max(1, params.target_fps);
  params.ctrl_interval = std::max(1, params.ctrl_interval);
  params.cam_distance = std::max(0.5, params.cam_distance);
  // Ensure R > r > 0
  params.torus_R = std::max(0.1, params.torus_R);
  params.torus_r = std::max(0.05, params.torus_r);
  if (params.torus_r >= params.torus_R) params.torus_r = std::max(0.05, params.torus_R * 0.4);
  double s = params.w_fps + params.w_quality;
  if (s <= 0.0) { params.w_fps = 0.5; params.w_quality = 0.5; }
}

static std::string make_ramp(int ramp_size) {
  // Expand default ramp to requested size by interpolation
  std::string base = DEFAULT_RAMP;
  if (ramp_size == (int)base.size()) return base;
  std::string ramp;
  ramp.reserve(ramp_size);
  for (int i = 0; i < ramp_size; ++i) {
    double t = (ramp_size == 1) ? 0.0 : (double)i / (double)(ramp_size - 1);
    double idx = t * (base.size() - 1);
    int i0 = (int)std::floor(idx);
    int i1 = std::min((int)base.size() - 1, i0 + 1);
    double u = idx - i0;
    // nearest for simplicity
    char c = (u < 0.5) ? base[i0] : base[i1];
    ramp.push_back(c);
  }
  return ramp;
}

static void clear_screen() {
  std::cout << "\x1b[2J\x1b[H"; // clear and home
}

static void draw_frame(const std::vector<char>& buf, int w, int h) {
  for (int y = 0; y < h; ++y) {
    std::cout.write(&buf[y * w], w);
    std::cout << '\n';
  }
}

static FrameStats measure_frame_time(const std::chrono::steady_clock::time_point& start,
                                     const std::chrono::steady_clock::time_point& end) {
  using namespace std::chrono;
  double ms = duration_cast<duration<double, std::milli>>(end - start).count();
  double fps = (ms > 0.0) ? 1000.0 / ms : 0.0;
  return FrameStats{fps, ms};
}

// Classic ASCII donut projection with rotation (adapted to C++)
static void render_torus_frame(std::vector<char>& out_buf,
                               std::vector<double>& zbuf,
                               int w, int h,
                               double A, double B,
                               const TorusModel& model,
                               const std::string& ramp,
                               double gamma,
                               double cam_distance) {
  std::fill(out_buf.begin(), out_buf.end(), ' ');
  std::fill(zbuf.begin(), zbuf.end(), 0.0);

  const double R = model.R;
  const double r = model.r;

  const double cosA = std::cos(A), sinA = std::sin(A);
  const double cosB = std::cos(B), sinB = std::sin(B);

  // Light direction (fixed)
  const double lx = 0.0, ly = 1.0, lz = -1.0;

  // Screen center and scale
  const double K1 = 20.0; // perspective scale
  const double K2 = cam_distance;  // camera distance

  for (double theta = 0.0; theta < 2 * M_PI; theta += 0.07) {        // around the tube
    const double costh = std::cos(theta), sinth = std::sin(theta);
    for (double phi = 0.0; phi < 2 * M_PI; phi += 0.02) {            // around the torus
      const double cosph = std::cos(phi), sinph = std::sin(phi);

      // Torus point in 3D before rotation
      double cx = (R + r * costh) * cosph;
      double cy = (R + r * costh) * sinph;
      double cz = r * sinth;

      // Rotate around X (A) and Z (B)
      double x = cx * cosB - cy * sinB;
      double y = cx * sinB + cy * cosB;
      double z = cz;

      double y2 = y * cosA - z * sinA;
      double z2 = y * sinA + z * cosA;

      double ooz = 1.0 / (z2 + K2); // one over z

      int xp = (int)(w / 2 + K1 * ooz * x);
      int yp = (int)(h / 2 + K1 * ooz * y2 * 0.5);

      // Normal for shading (approx)
      // Derive surface normal in model space and rotate similarly
      double nx = costh * cosph;
      double ny = costh * sinph;
      double nz = sinth;
      // rotate normal
      double nx_rz = nx * cosB - ny * sinB;
      double ny_rz = nx * sinB + ny * cosB;
      double nz_rz = nz;
      double nny = ny_rz * cosA - nz_rz * sinA;
      double nnz = ny_rz * sinA + nz_rz * cosA;
      double nnx = nx_rz;

      double L = nnx * lx + nny * ly + nnz * lz; // [-sqrt3, sqrt3]
      L = std::max(0.0, L);
      // gamma correction for ASCII ramp mapping
      double shade = std::pow(L, (gamma > 0.0 ? (1.0 / gamma) : 1.0));
      int idx = (int)std::floor(shade * (ramp.size() - 1));
      idx = std::clamp(idx, 0, (int)ramp.size() - 1);

      if (xp >= 0 && xp < w && yp >= 0 && yp < h) {
        double zb = ooz; // larger is nearer
        int off = yp * w + xp;
        if (zb > zbuf[off]) {
          zbuf[off] = zb;
          out_buf[off] = ramp[idx];
        }
      }
    }
  }
}

static double evaluate_score(const mcik_ctrl::ParamVector& pv,
                             double A, double B,
                             const TorusModel& torus,
                             int base_w, int base_h,
                             int target_fps,
                             double w_fps, double w_quality,
                             double cam_distance) {
  const int w = std::max(10, (int)std::round(base_w * pv.resolution_scale));
  const int h = std::max(10, (int)std::round(base_h * pv.resolution_scale));
  std::string ramp = make_ramp(pv.ramp_size);
  std::vector<char> buf(w * h, ' ');
  std::vector<double> zb(w * h, 0.0);
  auto t0 = std::chrono::steady_clock::now();
  render_torus_frame(buf, zb, w, h, A, B, torus, ramp, pv.gamma, cam_distance);
  auto t1 = std::chrono::steady_clock::now();
  FrameStats st = measure_frame_time(t0, t1);
  double q = torus_metrics::estimate_ascii_quality(buf, w, h);
  double fps_norm = std::min(st.fps / std::max(1, target_fps), 1.0);
  double score = w_fps * fps_norm + w_quality * q;
  return score;
}

// Non-blocking keyboard
static termios orig_termios;
static bool raw_enabled = false;

static void enable_raw_mode() {
  if (raw_enabled) return;
  termios raw;
  if (tcgetattr(STDIN_FILENO, &orig_termios) == -1) return;
  raw = orig_termios;
  raw.c_lflag &= ~(ICANON | ECHO);
  raw.c_cc[VMIN] = 0;
  raw.c_cc[VTIME] = 0;
  tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
  int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
  raw_enabled = true;
}

static void disable_raw_mode() {
  if (!raw_enabled) return;
  tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
  int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, flags & ~O_NONBLOCK);
  raw_enabled = false;
}

static int read_key_nonblock() {
  unsigned char c;
  ssize_t n = read(STDIN_FILENO, &c, 1);
  if (n == 1) return c;
  return -1;
}

static void synergy_demo(const RenderParams& params_base) {
  RenderParams params = params_base;
  const int w0 = params.base_width;
  const int h0 = params.base_height;
  TorusModel torus; torus.R = params.torus_R; torus.r = params.torus_r;
  double A = 0.6, B = 0.4; // fixed angles
  mcik_ctrl::ParamVector pv{params.resolution_scale, params.samples_per_pixel,
                            params.gamma, params.normal_smooth, params.ramp_size};
  auto eval = [&](const mcik_ctrl::ParamVector& test){
    return evaluate_score(test, A, B, torus, w0, h0, params.target_fps, params.w_fps, params.w_quality, params.cam_distance);
  };

  double s0 = eval(pv);
  mcik_ctrl::StepSuggestion k = mcik_ctrl::suggest_step(pv, eval, false);
  mcik_ctrl::StepSuggestion kh = mcik_ctrl::suggest_step(pv, eval, true);
  double sk = eval(k.next);
  double skh = eval(kh.next);

  std::cout << "Synergy demo (fixed scene)\n";
  std::cout << "Base score:" << std::fixed << std::setprecision(3) << s0 << "\n";
  std::cout << "K-only  score:" << sk << "  d=" << (sk - s0)
            << "  params:[scale=" << k.next.resolution_scale << ", spp=" << k.next.samples_per_pixel
            << ", gamma=" << k.next.gamma << ", ramp=" << k.next.ramp_size << "]\n";
  std::cout << "K+H    score:" << skh << "  d=" << (skh - s0)
            << "  params:[scale=" << kh.next.resolution_scale << ", spp=" << kh.next.samples_per_pixel
            << ", gamma=" << kh.next.gamma << ", ramp=" << kh.next.ramp_size << "]\n";
}

struct BenchStats { double avg_fps=0, avg_q=0, avg_sim=0; };

static BenchStats run_session(RenderParams params,
                              const std::vector<char>& ref,
                              int rw, int rh,
                              const TorusModel& torus,
                              int frames) {
  const int w0 = params.base_width, h0 = params.base_height;
  int w = (int)std::round(w0 * params.resolution_scale);
  int h = (int)std::round(h0 * params.resolution_scale);
  std::string ramp = make_ramp(params.ramp_size);
  std::vector<char> buffer(w * h);
  std::vector<double> zbuffer(w * h);
  double A=0.0, B=0.0, dA=0.05, dB=0.03;
  mcik_ctrl::ParamVector pv{params.resolution_scale, params.samples_per_pixel,
                            params.gamma, params.normal_smooth, params.ramp_size};
  bool useH = (params.controller == "KH");

  double sum_fps=0, sum_q=0, sum_sim=0;
  for (int f=0; f<frames; ++f) {
    auto t0 = std::chrono::steady_clock::now();
    render_torus_frame(buffer, zbuffer, w, h, A, B, torus, ramp, params.gamma, params.cam_distance);
    auto t1 = std::chrono::steady_clock::now();
    FrameStats st = measure_frame_time(t0, t1);
    double q = torus_metrics::estimate_ascii_quality(buffer, w, h);
    double sim = 0.0;
    if (w == rw && h == rh) sim = torus_metrics::estimate_ascii_similarity(buffer, ref, w, h);
    sum_fps += st.fps; sum_q += q; sum_sim += sim;

    if (params.controller != "off" && (f % std::max(1, params.ctrl_interval) == 0)) {
      auto eval = [&](const mcik_ctrl::ParamVector& test){
        return evaluate_score(test, A, B, torus, w0, h0, params.target_fps, params.w_fps, params.w_quality, params.cam_distance);
      };
      mcik_ctrl::StepSuggestion ss = mcik_ctrl::suggest_step(pv, eval, useH);
      pv = ss.next;
      params.resolution_scale = pv.resolution_scale;
      params.samples_per_pixel = pv.samples_per_pixel;
      params.gamma = pv.gamma;
      params.normal_smooth = pv.normal_smooth;
      params.ramp_size = pv.ramp_size;
      ramp = make_ramp(params.ramp_size);
      w = (int)std::round(w0 * params.resolution_scale);
      h = (int)std::round(h0 * params.resolution_scale);
      buffer.assign(w*h,' ');
      zbuffer.assign(w*h,0.0);
    }
    A += dA; B += dB;
  }
  BenchStats bs;
  double inv = frames > 0 ? 1.0/frames : 0.0;
  bs.avg_fps = sum_fps * inv;
  bs.avg_q = sum_q * inv;
  bs.avg_sim = sum_sim * inv;
  return bs;
}

static void benchmark(const RenderParams& params_base) {
  RenderParams params = params_base;
  const int w0 = params.base_width, h0 = params.base_height;
  TorusModel torus; torus.R = params.torus_R; torus.r = params.torus_r;
  // reference frame
  std::string rramp = make_ramp(16);
  std::vector<char> ref(w0*h0,' ');
  std::vector<double> rzb(w0*h0,0.0);
  render_torus_frame(ref, rzb, w0, h0, 0.6, 0.4, torus, rramp, 1.0, params.cam_distance);

  int frames = std::max(60, params.frames);
  std::cout << "Benchmark over " << frames << " frames per mode\n";

  std::ofstream csv;
  if (!params.log_csv.empty()) {
    csv.open(params.log_csv);
    if (csv.is_open()) {
      csv << "mode,avg_fps,avg_q,avg_sim\n";
    }
  }

  // OFF
  params.controller = "off";
  BenchStats off = run_session(params, ref, w0, h0, torus, frames);
  std::cout << "off  : fps=" << (int)std::round(off.avg_fps)
            << " q=" << std::fixed << std::setprecision(3) << off.avg_q
            << " sim=" << off.avg_sim << "\n";
  if (csv.is_open()) csv << "off," << off.avg_fps << "," << off.avg_q << "," << off.avg_sim << "\n";

  // K
  params.controller = "K";
  BenchStats k = run_session(params, ref, w0, h0, torus, frames);
  std::cout << "K    : fps=" << (int)std::round(k.avg_fps)
            << " q=" << k.avg_q
            << " sim=" << k.avg_sim << "\n";
  if (csv.is_open()) csv << "K," << k.avg_fps << "," << k.avg_q << "," << k.avg_sim << "\n";

  // K+H
  params.controller = "KH";
  BenchStats kh = run_session(params, ref, w0, h0, torus, frames);
  std::cout << "K+H  : fps=" << (int)std::round(kh.avg_fps)
            << " q=" << kh.avg_q
            << " sim=" << kh.avg_sim << "\n";
  if (csv.is_open()) csv << "KH," << kh.avg_fps << "," << kh.avg_q << "," << kh.avg_sim << "\n";
}

int main(int argc, char** argv) {
  RenderParams params;
  parse_args(argc, argv, params);

  if (params.mode == "synergy") {
    synergy_demo(params);
    return 0;
  }
  if (params.mode == "benchmark") {
    benchmark(params);
    return 0;
  }

  const int w0 = params.base_width;
  const int h0 = params.base_height;
  const int w = (int)std::round(w0 * params.resolution_scale);
  const int h = (int)std::round(h0 * params.resolution_scale);
  std::string ramp = make_ramp(params.ramp_size);

  std::vector<char> buffer(w * h, ' ');
  std::vector<double> zbuffer(w * h, 0.0);

  TorusModel torus; torus.R = params.torus_R; torus.r = params.torus_r;
  Camera cam; cam.distance = params.cam_distance;

  using clock = std::chrono::steady_clock;

  double A = 0.0, B = 0.0; // rotation angles
  const double dA = 0.05, dB = 0.03;

  const bool interactive = (params.mode == "interactive");
  const int frames = interactive ? INT_MAX : std::max(1, params.frames);

  // Build a high-quality reference at startup (full scale, gamma 1.0, large ramp)
  const int rw = w0;
  const int rh = h0;
  std::string rramp = make_ramp(16);
  std::vector<char> ref(rw * rh, ' ');
  std::vector<double> rzb(rw * rh, 0.0);
  render_torus_frame(ref, rzb, rw, rh, 0.6, 0.4, torus, rramp, 1.0, cam.distance);

  // CSV logging (batch)
  std::ofstream csv;
  if (!interactive) {
    std::string path = params.log_csv;
    if (path.empty()) {
      auto now = clock::now().time_since_epoch();
      auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
      std::ostringstream oss;
      oss << "test_data/ascii_torus/log-" << ms << ".csv";
      path = oss.str();
    }
    csv.open(path);
    if (csv.is_open()) {
      csv << "frame,ms,fps,quality,similarity,scale,spp,gamma,ramp,controller\n";
    }
  }

  // Current controller params
  mcik_ctrl::ParamVector pv{params.resolution_scale, params.samples_per_pixel,
                            params.gamma, params.normal_smooth, params.ramp_size};
  const bool useH_initial = (params.controller == "KH");
  bool useH = useH_initial;

  if (interactive) enable_raw_mode();

  for (int f = 0; f < frames; ++f) {
    auto start = clock::now();

    // Hotkeys
    if (interactive) {
      int c;
      while ((c = read_key_nonblock()) != -1) {
        if (c == 'q' || c == 'Q') { disable_raw_mode(); return 0; }
        if (c == '1') { params.controller = "off"; }
        if (c == '2') { params.controller = "K"; useH = false; }
        if (c == '3') { params.controller = "KH"; useH = true; }
        if (c == '+') { params.target_fps = std::min(240, params.target_fps + 5); }
        if (c == '-') { params.target_fps = std::max(1, params.target_fps - 5); }
      }
    }

    clear_screen();

    // Render frame
    render_torus_frame(buffer, zbuffer, w, h, A, B, torus, ramp, params.gamma, cam.distance);

    // Quality metrics
    double quality_edge = torus_metrics::estimate_ascii_quality(buffer, w, h);
    double sim = 0.0;
    if (w == rw && h == rh) {
      sim = torus_metrics::estimate_ascii_similarity(buffer, ref, w, h);
    }

    // HUD
    auto mid = clock::now();
    FrameStats stats = measure_frame_time(start, mid);
    std::cout.setf(std::ios::fixed);
    std::cout.precision(2);
    std::cout << "FPS:" << (int)std::round(stats.fps)
              << "  target:" << params.target_fps
              << "  quality:" << quality_edge
              << "  sim:" << sim
              << "  params:[scale=" << params.resolution_scale
              << ", spp=" << params.samples_per_pixel
              << ", gamma=" << params.gamma
              << ", ramp=" << params.ramp_size
              << ", R=" << torus.R
              << ", r=" << torus.r
              << ", cam=" << cam.distance
              << "]  controller:" << (useH ? "K+H" : (params.controller == "K" ? "K" : "off"))
              << "  keys:[1/2/3 modes, +/- fps, q quit]\n";

    // Frame
    draw_frame(buffer, w, h);

    // Controller step every ctrl_interval frames (if enabled)
    if (params.controller != "off" && (f % params.ctrl_interval == 0)) {
      auto eval = [&](const mcik_ctrl::ParamVector& test){
        return evaluate_score(test, A, B, torus, w0, h0, params.target_fps, params.w_fps, params.w_quality, cam.distance);
      };
      mcik_ctrl::StepSuggestion ss = mcik_ctrl::suggest_step(pv, eval, useH);
      pv = ss.next;
      // Apply to live params
      params.resolution_scale = pv.resolution_scale;
      params.samples_per_pixel = pv.samples_per_pixel;
      params.gamma = pv.gamma;
      params.normal_smooth = pv.normal_smooth;
      params.ramp_size = pv.ramp_size;
      ramp = make_ramp(params.ramp_size);
    }

    // Batch CSV logging
    if (!interactive && csv.is_open()) {
      auto end = clock::now();
      FrameStats total = measure_frame_time(start, end);
      csv << f << "," << total.ms << "," << total.fps << "," << quality_edge << "," << sim << ","
          << params.resolution_scale << "," << params.samples_per_pixel << ","
          << params.gamma << "," << params.ramp_size << ","
          << (useH ? "K+H" : (params.controller == "K" ? "K" : "off")) << "\n";
    }

    // Advance rotation
    A += dA; B += dB;

    // Sleep to aim for target FPS in interactive mode
    if (interactive) {
      auto end = clock::now();
      FrameStats total = measure_frame_time(start, end);
      double target_ms = 1000.0 / params.target_fps;
      if (total.ms < target_ms) {
        auto to_sleep = std::chrono::duration<double, std::milli>(target_ms - total.ms);
        std::this_thread::sleep_for(to_sleep);
      }
    }
  }

  if (interactive) disable_raw_mode();

  return 0;
}
