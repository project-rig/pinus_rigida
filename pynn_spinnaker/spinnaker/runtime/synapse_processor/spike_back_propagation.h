#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::SpikeBackPropagation
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
class SpikeBackPropagation
{
public:
  SpikeBackPropagation() : m_KeyPopulationMask(0), m_KeyPopulationKey(0),
    m_KeyVertexMask(0), m_KeyVertexStartKey(0), m_KeyVertexStopKey(0),
    m_KeyVertexShift(0), m_VertexStride(0), m_KeyNeuronMask(0)
  {
  }

  //--------------------------------------------------------------------------
  // Public API
  //--------------------------------------------------------------------------
  bool GetLocalNeuronIndex(uint32_t key, unsigned int &localIndex)
  {
    // If population component of key doesn't match, return false
    if((key & m_KeyPopulationMask) != m_KeyPopulationKey)
    {
      return false;
    }

    // If key comes from a vertex beyond the range we're interested in, return false
    const uint32_t keyVertex = (key & m_KeyVertexMask);
    if(keyVertex < m_KeyVertexStartKey || keyVertex > m_KeyVertexStopKey)
    {
      return false;
    }

    // Subtract key start
    const uint32_t localVertexIndex = (keyVertex - m_KeyVertexStartKey) >> m_KeyVertexShift;

    // Finally mask out source neuron index from key and add to strided local vertex index
    // **NOTE** assumed to be at bottom of mask
    localIndex = (unsigned int)((key & m_KeyNeuronMask) + (localVertexIndex * m_VertexStride));
    return true;
  }

  bool ReadSDRAMData(uint32_t *region, uint32_t)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "SpikeBackPropagation::ReadSDRAMData");

    // Read configuration words
    m_KeyPopulationMask = *region++;
    m_KeyPopulationKey = *region++;

    m_KeyVertexMask = *region++;
    m_KeyVertexStartKey = *region++;
    m_KeyVertexStopKey = *region++;
    m_KeyVertexShift = *region++;
    m_VertexStride = *region++;

    m_KeyNeuronMask = *region++;

    LOG_PRINT(LOG_LEVEL_INFO, "\tKey population mask:%08x, Key population key:%08x",
      m_KeyPopulationMask, m_KeyPopulationKey);

    LOG_PRINT(LOG_LEVEL_INFO, "\tKey vertex mask:%08x, Key vertex start key:%08x, Key vertex stop key:%08x, Key vertex shift:%u, Vertex stride:%u",
      m_KeyVertexMask, m_KeyVertexStartKey, m_KeyVertexStopKey, m_KeyVertexShift, m_VertexStride);

    LOG_PRINT(LOG_LEVEL_INFO, "\tKey neuron mask:%08x", m_KeyNeuronMask);
    return true;
  }

private:
  //--------------------------------------------------------------------------
  // Members
  //--------------------------------------------------------------------------
  // Mask to extract population index from spike key and key to match
  // it against to determine if spike comes from back-propogating population
  uint32_t m_KeyPopulationMask;
  uint32_t m_KeyPopulationKey;

  // Mask and shift to extract vertex index from spike key
  uint32_t m_KeyVertexMask;
  uint32_t m_KeyVertexStartKey;
  uint32_t m_KeyVertexStopKey;
  uint32_t m_KeyVertexShift;

  // How many neurons does each vertex contain
  uint32_t m_VertexStride;

  // Mask to extract neuron index from spike key
  uint32_t m_KeyNeuronMask;
};
}