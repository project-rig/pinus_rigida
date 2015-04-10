#ifndef LOG_H
#define LOG_H

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
// Log levels
#define LOG_LEVEL_TRACE 0
#define LOG_LEVEL_INFO  1
#define LOG_LEVEL_WARN  2
#define LOG_LEVEL_ERROR 3

// Default log level
#ifndef LOG_LEVEL
  #define LOG_LEVEL LOG_LEVEL_ERROR
#endif

// Log print function
#define LOG_PRINT(level, s, ...)                    \
  do                                                \
  {                                                 \
#if level >= LOG_LEVEL                              \
    io_printf(IO_BUF, "["#level"]"s, ##__VA_ARGS__);\
#endif  // level >= LOG_LEVEL                       \
  } while (0)

#endif  // LOG_H