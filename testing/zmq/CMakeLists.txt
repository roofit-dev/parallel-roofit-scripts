cmake_minimum_required(VERSION 3.0)
project(zmq_testing VERSION 0.0.2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
find_package(ZeroMQ REQUIRED)

add_library(utils utils.cpp)

add_executable(pubsub_vs_many_pipes pubsub_vs_many_pipes.cpp)
target_link_libraries(pubsub_vs_many_pipes PRIVATE ${ZeroMQ_LIBRARY} utils)
target_include_directories(pubsub_vs_many_pipes PRIVATE ${ZeroMQ_INCLUDE_DIR})

add_executable(double_bind double_bind.cpp)
target_link_libraries(double_bind PRIVATE ${ZeroMQ_LIBRARY} utils)
target_include_directories(double_bind PRIVATE ${ZeroMQ_INCLUDE_DIR})
