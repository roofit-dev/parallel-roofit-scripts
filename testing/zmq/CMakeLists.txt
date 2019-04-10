cmake_minimum_required(VERSION 3.0)
project(zmq_testing VERSION 0.0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)

add_executable(pubsub_vs_many_pipes pubsub_vs_many_pipes.cpp)

find_package(ZeroMQ REQUIRED)
target_link_libraries(pubsub_vs_many_pipes PRIVATE ${ZeroMQ_LIBRARY})
target_include_directories(pubsub_vs_many_pipes PRIVATE ${ZeroMQ_INCLUDE_DIR})
