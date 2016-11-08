#pragma once

// Standard includes
#include <cstdint>

// Connection builder includes
#include "generator_factory.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::Random;

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
// Forward declarations
namespace ConnectorGenerator
{
  class Base;
}

namespace ParamGenerator
{
  class Base;
}

namespace MatrixGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  Base(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual bool Generate(uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
    unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
    unsigned int sizeWords, unsigned int numRows,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const = 0;

protected:
  //-----------------------------------------------------------------------------
  // Protected methods
  //-----------------------------------------------------------------------------
  void TraceUInt(uint32_t (&values)[1024], unsigned int number) const;
  void TraceInt(int32_t (&values)[1024], unsigned int number) const;

  unsigned int GenerateRow(unsigned int row,
    unsigned int weightFixedPoint, unsigned int numPostNeurons,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    uint32_t (&indices)[1024], int32_t (&delay)[1024], int32_t (&weight)[1024],
    MarsKiss64 &rng) const;

  int32_t ClampWeight(int32_t weight) const
  {
    // If weights aren't signed and weight is negative, zero
    // **NOTE** negative weights caused by inhibitory
    // weights should have been already flipped in host
    return (!m_SignedWeight && weight < 0) ? 0 : weight;
  }

  int32_t ClampDelay(int32_t delay) const
  {
    // If delay is lower than minimum (1 timestep), clamp
    return (delay < 1) ? 1 : delay;
  }

  bool IsSignedWeight() const{ return m_SignedWeight; }


  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayBits = 3;
  static const uint32_t IndexBits = 10;
  static const uint32_t DelayMask = ((1 << DelayBits) - 1);
  static const uint32_t IndexMask = ((1 << IndexBits) - 1);

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_SignedWeight;
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
  virtual bool Generate(uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
    unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
    unsigned int sizeWords, unsigned int numRows,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const;

private:
  Static(uint32_t *&region);
};

//-----------------------------------------------------------------------------
// Plastic
//-----------------------------------------------------------------------------
class Plastic : public Base
{
public:
  ADD_FACTORY_CREATOR(Plastic);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual bool Generate(uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
    unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
    unsigned int sizeWords, unsigned int numRows,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const;

private:
  Plastic(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_PreStateWords;
  uint32_t m_SynapseTraceBytes;
};
} // MatrixGenerator
} // ConnectionBuilder