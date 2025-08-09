
cmake_minimum_required(VERSION 3.22)

# Set toolchain to RISC-V; must be done before call to project()
include($ENV{FP_SDK_PATH}/cmake/riscv-toolchain.cmake)

project(driver
  LANGUAGES C
  DESCRIPTION "A GameTime test for the WCET of a function"
  VERSION 1.0.0
)

set(DEBUG true)
set(CMAKE_BUILD_TYPE "Debug")
# Use -O0 to disable compiler optimization
set(CMAKE_C_FLAGS "-g -O0 -static -march=rv32i_zicsr -mabi=ilp32 -nostartfiles --specs=nosys.specs -ffunction-sections -fdata-sections -Wl,--gc-sections")

add_executable(driver driver.c)

include($ENV{FP_SDK_PATH}/cmake/fp-app.cmake)

# Add sdk as subdirectory out-of-tree and link it
add_subdirectory($ENV{FP_SDK_PATH} BINARY_DIR)
target_link_libraries(driver fp-sdk)

fp_add_outputs(driver)
        