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
// ConnectionBuilder::ConnectorGenerators
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace ConnectorGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
//! Base class for all connector generators
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  //! Generates the list of postsynaptic neuron indices which a given row
  //! i.e. presynaptic neuron should connect to.
  //!   \param row              what row of the submatrix are we generating?
  //!                           i.e. what is the index of the presynaptic neuron?
  //!   \param numPostNeurons   how many postsynaptic neurons will the synapse
  //!                           processor which ultimately uses this synaptic
  //!                           matrix provide synaptic input for.
  //!   \param vertexPostSlice  integer specifying the postsynaptic 'coordinate'
  //!                           of submatrix being generated within the full
  //!                           synaptic matrix between two populations.
  //!   \param rng              random number generator to use, if required.
  //!   \param indices          reference to array to write generated parameters to.
  virtual unsigned int Generate(unsigned int row, unsigned int numPostNeurons,
                                unsigned int vertexPostSlice, unsigned int vertexPreSlice,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]) = 0;

};

//-----------------------------------------------------------------------------
// AllToAll
//-----------------------------------------------------------------------------
//! Connector generator for connections where each neuron in the presynaptic
//! population is connected to *all* neurons in the postsynaptic population.
class AllToAll : public Base
{
public:
  ADD_FACTORY_CREATOR(AllToAll);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int numPostNeurons,
                                unsigned int vertexPostSlice, unsigned int vertexPreSlice,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]);

private:
  AllToAll(uint32_t *&);

  //-----------------------------------------------------------------------------
  // Members
  //----------------------------------------------------------------------------
  //! Should self connections i.e. between neurons and themselves be made
  uint32_t m_AllowSelfConnections;
};

//-----------------------------------------------------------------------------
// OneToOne
//-----------------------------------------------------------------------------
//! Connector generator for connections where each neuron in the presynaptic
//! population is connected to the neuron with the same index in the
//! (equally-sized) postsynaptic population.
class OneToOne : public Base
{
public:
  ADD_FACTORY_CREATOR(OneToOne);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int numPostNeurons,
                                unsigned int vertexPostSlice, unsigned int vertexPreSlice,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]);

private:
  OneToOne(uint32_t *&);
};

//-----------------------------------------------------------------------------
// FixedProbability
//-----------------------------------------------------------------------------
class FixedProbability : public Base
{
public:
  ADD_FACTORY_CREATOR(FixedProbability);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int numPostNeurons,
                                unsigned int vertexPostSlice, unsigned int vertexPreSlice,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]);

private:
  FixedProbability(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Probability (in U032 fixed-point format) of any
  //! pair of pre and postsynaptic neurons being connected
  uint32_t m_Probability;

  //! Should self connections i.e. between neurons and themselves be made
  uint32_t m_AllowSelfConnections;
};

//-----------------------------------------------------------------------------
// FixedTotalNumber
//-----------------------------------------------------------------------------
class FixedTotalNumber : public Base
{
public:
  ADD_FACTORY_CREATOR(FixedTotalNumber);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int numPostNeurons,
                                unsigned int vertexPostSlice, unsigned int vertexPreSlice,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]);

private:
  FixedTotalNumber(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Should self connections i.e. between neurons and themselves be made
  uint32_t m_AllowSelfConnections;


  uint32_t m_WithReplacement;
  uint32_t m_ConnectionsInSubmatrix;
  uint32_t m_SubmatrixSize;
};

} // ConnectorGenerators
} // ConnectionBuilder
