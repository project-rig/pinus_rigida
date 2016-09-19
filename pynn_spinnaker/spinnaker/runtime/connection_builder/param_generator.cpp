#include "param_generator.h"

// Common includes
#include "../common/random/mars_kiss64.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator::Constant
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Constant::Generate(unsigned int number,
  unsigned int, MarsKiss64 &, int32_t (&output)[1024])
{
  // Copy constant into output
  for(uint32_t i = 0; i < number; i++)
  {
    output[i] = m_Constant;
  }
}
//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerators::Uniform
//-----------------------------------------------------------------------------
void ConnectionBuilder::ParamGenerator::Uniform::Generate(unsigned int number,
  unsigned int, MarsKiss64 &rng, int32_t (&output)[1024])
{
  // Copy constant into output
  for(uint32_t i = 0; i < number; i++)
  {
    output[i] = 3;
  }
}