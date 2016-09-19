#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/log.h"

// Connection builder includes
#include "generator_factory.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace MatrixGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowWords,
    unsigned int weightFixedPoint/*,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng*/) const = 0;
};

//-----------------------------------------------------------------------------
// Static
//-----------------------------------------------------------------------------
class Static : public Base
{
public:
  ADD_FACTORY_CREATOR(Static);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowWords,
    unsigned int weightFixedPoint/*,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng*/) const;

private:
  Static(uint32_t *&region)
  {
    m_NumRows = *region++;
    LOG_PRINT(LOG_LEVEL_INFO, "\tStatic synaptic matrix: num rows:%u", m_NumRows);
  }

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayBits = 3;
  static const uint32_t IndexBits = 10;
  static const uint32_t DelayMask = ((1 << DelayBits) - 1);
  static const uint32_t IndexMask = ((1 << IndexBits) - 1);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_NumRows;
};

} // MatrixGenerator
} // ConnectionBuilder