cmake_minimum_required(VERSION 3.16)
project(mcik_ascii_torus CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ASCII torus renderer
add_executable(ascii_torus
  experiments/ascii_torus/cpp/ascii_torus.cpp
)

target_include_directories(ascii_torus PRIVATE
  experiments/ascii_torus/cpp
)

# Reasonable default flags for release-like build if none provided
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

if(MSVC)
  target_compile_options(ascii_torus PRIVATE /W4)
else()
  target_compile_options(ascii_torus PRIVATE -O2 -Wall -Wextra -Wpedantic)
endif()
