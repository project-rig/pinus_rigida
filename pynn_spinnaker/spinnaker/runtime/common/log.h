#pragma once

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
// Log levels
#define LOG_LEVEL_TRACE 0
#define LOG_LEVEL_INFO  1
#define LOG_LEVEL_WARN  2
#define LOG_LEVEL_ERROR 3
#define LOG_LEVEL_DISABLED 4

// Default log level
#ifndef LOG_LEVEL
  #define LOG_LEVEL LOG_LEVEL_INFO
#endif

// Log print function
#define LOG_PRINT(level, s, ...)                                \
  do                                                            \
  {                                                             \
    if(level >= LOG_LEVEL)                                      \
    {                                                           \
      io_printf(IO_BUF, "[" #level "] " s "\n", ##__VA_ARGS__); \
    }                                                           \
  } while(false)
