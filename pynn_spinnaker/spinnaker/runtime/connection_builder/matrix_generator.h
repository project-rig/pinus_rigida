#pragma once

// Standard include
#include <algorithm>
#include <cstdint>

// Common includes
#include "../common/row_offset_length.h"

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
//! Base class for all matrix-generators. Provides an interface to generate a
//! synaptic matrix of the format specified by the connection builder using
//! the specified connector, delay and weight generators.
class Base
{
public:
  Base(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  //! Generate a synaptic matrix
  //!   \param synapticMatrixBaseAddress  Where in SDRAM does the synaptic
  //!                                     matrix region begin (required because
  //!                                     delay-row offsets are calculated from this).
  //!   \param matrixAddress              Where in SDRAM to start writing matrix
  //!   \param maxRowSynapses             What is the maximum length of rows (in
  //!                                     synapses) in the ragged section of
  //!                                     the synaptic matrix.
  //!   \param weightFixedPoint           Where is the fixed point located in the
  //!                                     weight format used to represent weights.
  //!   \param numPostNeurons             How many postsynaptic neurons will
  //!                                     the synapse processor, destined for this
  //!                                     core generate input for.
  //!   \param sizeWords                  How large is the space allocated for
  //!                                     this synaptic matrix (in words)connectorGenerator
  //!   \param numRows                    How many rows does this synaptic matrix have
  //!   \param vertexPostSlice            What neuron index (in terms of the whole
  //!                                     population) will the postsynaptic neurons
  //!                                     the synapse processors, destined for this
  //!                                     core start from.
  //!   \param vertexPreSlice             What neuron index (in terms of the whole
  //!                                     presynaptic population) does this
  //!                                     synaptic matrix start from.
  //!   \param connectorGenerator         Connector generator to generate indices
  //!                                     for rows of this matrix.
  //!   \param delayGenerator             Param generator to generate delays for
  //!                                     synapses in this submatrix.
  //!   \param weightGenerator            Param generator to generate weights for
  //!                                     synapses in this submatrix.
  //!   \param rng                        Random number generator to use for all
  //!                                     stochastic operations in this matrix
  bool Generate(uint32_t *synapticMatrixBaseAddress, uint32_t *matrixAddress,
    unsigned int maxRowSynapses, unsigned int weightFixedPoint, unsigned int numPostNeurons,
    unsigned int sizeWords, unsigned int numRows,
    unsigned int vertexPostSlice, unsigned int vertexPreSlice,
    ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const;

protected:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  //! Write a sub-row to memory based on a subset of the indices, delays and weights
  //!   \param rowAddress       SDRAM address to write row to
  //!   \param startDelay       What is the start delay (in time steps)
  //!                           this sub-row can represent
  //!   \param subRowStartIndex Pointer to start of array of indices used to
  //!                           extract desired sub-row from indices, delays and weights
  //!   \param subRowEndIndex   Pointer to end of array of indices used to
  //!                           extract desired sub-row from indices, delays and weights
  //!   \param indices          Indices of postsynaptic neurons row connects to
  //!                           (generated by connector generator)
  //!   \param delays           Delays associated with each synapse in row
  //!                           (generated by parameter generator)
  //!   \param weights          Weights associated with each synapse in row
  //!                           (generated by parameter generator)
  //!   \return Number of words written to row
  virtual unsigned int WriteRow(uint32_t *rowAddress, int32_t startDelay,
    const uint16_t *subRowStartIndex, const uint16_t *subRowEndIndex,
    const uint32_t (&indices)[1024], const int32_t (&delays)[1024], const int32_t (&weights)[1024]) const = 0;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const = 0;

  //-----------------------------------------------------------------------------
  // Protected methods
  //-----------------------------------------------------------------------------
  void TraceUInt(uint32_t (&values)[1024], unsigned int number) const;
  void TraceInt(int32_t (&values)[1024], unsigned int number) const;

  int32_t ClampWeight(int32_t weight) const
  {
    if(IsSignedWeight())
    {
      return std::max<int32_t>(INT16_MIN,
                               std::min<int32_t>(INT16_MAX, weight));
    }
    // Otherwise, if weights aren't signed and weight is negative, zero
    // **NOTE** negative weights caused by inhibitory
    // weights should have been already flipped in host
    else
    {
      return std::max<int32_t>(0,
                               std::min<int32_t>(UINT16_MAX, weight));
    }
  }

  int32_t ClampDelay(int32_t delay) const
  {
    // If delay is lower than minimum (1 timestep), clamp
    return (delay < 1) ? 1 : delay;
  }

  bool IsSignedWeight() const{ return (m_SignedWeight != 0); }


  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayBits = 3;
  static const uint32_t IndexBits = 10;
  static const uint32_t DelayMask = ((1 << DelayBits) - 1);
  static const uint32_t IndexMask = ((1 << IndexBits) - 1);

  static const uint32_t NumHeaderWords = 3;
  static const uint32_t MaxDTCMDelaySlots = 7;

  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef Common::RowOffsetLength<IndexBits> RowOffsetLength;

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

protected:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int WriteRow(uint32_t *rowAddress, int32_t startDelay,
    const uint16_t *subRowStartIndex, const uint16_t *subRowEndIndex,
    const uint32_t (&indices)[1024], const int32_t (&delays)[1024], const int32_t (&weights)[1024]) const;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const;

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

protected:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int WriteRow(uint32_t *rowAddress, int32_t startDelay,
    const uint16_t *subRowStartIndex, const uint16_t *subRowEndIndex,
    const uint32_t (&indices)[1024], const int32_t (&delays)[1024], const int32_t (&weights)[1024]) const;

  virtual unsigned int GetMaxRowWords(unsigned int maxRowSynapses) const;

private:
  Plastic(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Private methods
  //-----------------------------------------------------------------------------
  unsigned int GetNumPlasticWords(unsigned int numSynapses) const
  {
    // Calculate the size of the plastic part of row
    const unsigned int numPlasticArrayBytes = numSynapses * (2 + m_SynapseTraceBytes);

    return (numPlasticArrayBytes / 4) + (((numPlasticArrayBytes & 3) != 0) ? 1 : 0);
  }

  unsigned int GetNumControlWords(unsigned int numSynapses) const
  {
    // Calculate the size of the control part of row
    return (numSynapses / 2) + (((numSynapses & 1) != 0) ? 1 : 0);
  }
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_PreStateWords;
  uint32_t m_SynapseTraceBytes;
};
} // MatrixGenerator
} // ConnectionBuilder
