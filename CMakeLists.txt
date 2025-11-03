cmake_minimum_required(VERSION 3.16)
project(mcik LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(mcik_kernels INTERFACE)
target_include_directories(mcik_kernels INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/modules/cpp/include>
  $<INSTALL_INTERFACE:include>
)

add_executable(mcik_demo modules/cpp/src/main.cpp)
target_link_libraries(mcik_demo PRIVATE mcik_kernels)

add_executable(ascii_torus experiments/ascii_torus/cpp/ascii_torus.cpp)
target_link_libraries(ascii_torus PRIVATE mcik_kernels)

# Reasonable default flags for release-like build if none provided
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

if(MSVC)
  target_compile_options(mcik_demo PRIVATE /W4)
  target_compile_options(ascii_torus PRIVATE /W4)
else()
  target_compile_options(mcik_demo PRIVATE -O2 -Wall -Wextra -Wpedantic)
  target_compile_options(ascii_torus PRIVATE -O2 -Wall -Wextra -Wpedantic)
endif()
