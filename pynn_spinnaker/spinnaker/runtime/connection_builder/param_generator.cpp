#include "param_generator.h"

// Common includes
#include "../common/arm_intrinsics.h"
#include "../common/log.h"
#include "../common/random/mars_kiss64.h"

// Namespaces
using namespace Common::ARMIntrinsics;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator::Constant
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Constant::Constant(uint32_t *&region)
{
  m_Value = *reinterpret_cast<int32_t*>(region++);

  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tConstant parameter: value:%d", m_Value);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Constant::Generate(unsigned int number,
  unsigned int, MarsKiss64 &, int32_t (&output)[1024]) const
{
  // Copy constant into output
  for(uint32_t i = 0; i < number; i++)
  {
    output[i] = m_Value;
  }
}

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::Uniform
//-----------------------------------------------------------------------------
ConnectionBuilder::ParamGenerator::Uniform::Uniform(uint32_t *&region)
{
  m_Low = *reinterpret_cast<int32_t*>(region++);
  m_Range = *reinterpret_cast<int32_t*>(region++);
  LOG_PRINT(LOG_LEVEL_INFO, "\t\t\tUniform parameter: low:%d, range:%d",
            m_Low, m_Range);
}
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Uniform::Generate(unsigned int number,
  unsigned int, MarsKiss64 &rng, int32_t (&output)[1024]) const
{
  // Copy constant into output
  for(uint32_t i = 0; i < number; i++)
  {
    // Draw random number (0, UINT32_MAX) clear top bit and cast to signed
    int32_t fraction = (int32_t)(rng.GetNext() & 0x7FFFFFFF);

    // Multiply the resultant fraction by the range and shift down
    output[i] = m_Low + (int32_t)(__smull(fraction, m_Range) >> 31);
  }
}