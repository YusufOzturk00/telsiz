cmake_minimum_required(VERSION 3.20)
project(telsiz_loopback LANGUAGES CXX)

if(NOT WIN32)
    message(FATAL_ERROR "telsiz-loopback uses the Windows audio engine and only builds on Windows")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# Static C++ runtime: the exe runs without the Visual C++ Redistributable.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_executable(telsiz-loopback main.cpp)
target_compile_definitions(telsiz-loopback PRIVATE UNICODE _UNICODE NOMINMAX _WIN32_WINNT=0x0A00)
target_link_libraries(telsiz-loopback PRIVATE mmdevapi ole32 avrt)
if(MSVC)
    target_compile_options(telsiz-loopback PRIVATE /W4 /WX /permissive- /utf-8)
endif()
